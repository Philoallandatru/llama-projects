"""Deep Analysis Workflow 测试"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.workflows.deep_analysis import DeepAnalysisWorkflow, LoadIssueEvent, RouteEvent
from src.core.router import ProfileConfig


@pytest.fixture
def mock_jira_config():
    """Mock Jira 配置"""
    return {
        "server": "https://jira.example.com",
        "email": "test@example.com",
        "token": "test_token"
    }


@pytest.fixture
def mock_llm_config():
    """Mock LLM 配置"""
    return {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:14b",
        "temperature": 0.1,
        "max_tokens": 4096
    }


@pytest.fixture
def mock_issue_data():
    """Mock issue 数据"""
    return {
        "key": "TEST-123",
        "fields": {
            "summary": "Test issue",
            "description": "Test description",
            "issuetype": {"name": "Bug"},
            "status": {"name": "Open"},
            "priority": {"name": "High"},
            "created": "2024-01-01T00:00:00.000+0000",
            "updated": "2024-01-02T00:00:00.000+0000",
            "comment": {"comments": []}
        }
    }


@pytest.fixture
def mock_profile():
    """Mock profile 配置"""
    return ProfileConfig(
        name="rca",
        description="Root Cause Analysis",
        issue_types=["Bug"],
        prompt_template="rca",
        output_sections=["失效机制", "根本原因", "证据链", "差距分析", "建议"]
    )


@pytest.mark.asyncio
async def test_workflow_initialization(mock_jira_config, mock_llm_config, tmp_path):
    """测试工作流初始化"""
    workflow = DeepAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path
    )
    
    assert workflow.jira_config == mock_jira_config
    assert workflow.llm_config == mock_llm_config
    assert workflow.index_base_path == tmp_path


@pytest.mark.asyncio
async def test_start_step(mock_jira_config, mock_llm_config, tmp_path):
    """测试 start 步骤"""
    workflow = DeepAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path
    )
    
    # 创建 mock context
    ctx = MagicMock()
    ctx.data = {}
    
    # 创建 StartEvent
    from llama_index.core.workflow import StartEvent
    ev = StartEvent(issue_key="TEST-123", mode="balanced")
    
    # 执行 start 步骤
    result = await workflow.start(ctx, ev)
    
    # 验证
    assert isinstance(result, LoadIssueEvent)
    assert result.issue_key == "TEST-123"
    assert ctx.data["issue_key"] == "TEST-123"
    assert ctx.data["mode"] == "balanced"
    assert ctx.data["retrieve_evidence"] is True


@pytest.mark.asyncio
async def test_start_step_missing_issue_key(mock_jira_config, mock_llm_config, tmp_path):
    """测试 start 步骤缺少 issue_key"""
    workflow = DeepAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path
    )
    
    ctx = MagicMock()
    ctx.data = {}
    
    from llama_index.core.workflow import StartEvent
    ev = StartEvent()  # 没有 issue_key
    
    # 应该抛出 ValueError
    with pytest.raises(ValueError, match="issue_key is required"):
        await workflow.start(ctx, ev)


@pytest.mark.asyncio
async def test_load_issue_step(mock_jira_config, mock_llm_config, mock_issue_data, tmp_path):
    """测试 load_issue 步骤"""
    workflow = DeepAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path
    )
    
    ctx = MagicMock()
    ctx.data = {}
    ctx.write_event_to_stream = MagicMock()
    
    # Mock IssueLoader
    with patch('src.workflows.deep_analysis.IssueLoader') as MockLoader:
        mock_loader = MockLoader.return_value
        mock_loader.load_issue_realtime = AsyncMock(return_value=mock_issue_data)
        
        ev = LoadIssueEvent(issue_key="TEST-123")
        result = await workflow.load_issue(ctx, ev)
        
        # 验证
        assert isinstance(result, RouteEvent)
        assert result.issue_type == "Bug"
        assert ctx.data["issue_data"] == mock_issue_data
        ctx.write_event_to_stream.assert_called_once()


@pytest.mark.asyncio
async def test_route_profile_step(mock_jira_config, mock_llm_config, mock_profile, tmp_path):
    """测试 route_profile 步骤"""
    # 创建 profiles 配置
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    
    config_file = profiles_dir / "config.json"
    config_file.write_text("""{
        "profiles": {
            "rca": {
                "name": "rca",
                "description": "Root Cause Analysis",
                "issue_types": ["Bug"],
                "prompt_template": "rca",
                "output_sections": ["失效机制", "根本原因"]
            }
        },
        "default_profile": "rca"
    }""", encoding="utf-8")
    
    workflow = DeepAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=profiles_dir
    )
    
    ctx = MagicMock()
    ctx.data = {}
    ctx.write_event_to_stream = MagicMock()
    
    from src.workflows.deep_analysis import RetrieveEvent
    ev = RouteEvent(issue_type="Bug")
    result = await workflow.route_profile(ctx, ev)
    
    # 验证
    assert isinstance(result, RetrieveEvent)
    assert ctx.data["profile"].name == "rca"
    ctx.write_event_to_stream.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_evidence_skip(mock_jira_config, mock_llm_config, tmp_path):
    """测试跳过证据检索"""
    workflow = DeepAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path
    )
    
    ctx = MagicMock()
    ctx.data = {"retrieve_evidence": False}
    ctx.write_event_to_stream = MagicMock()
    
    from src.workflows.deep_analysis import RetrieveEvent, AnalyzeEvent
    ev = RetrieveEvent()
    result = await workflow.retrieve_evidence(ctx, ev)
    
    # 验证
    assert isinstance(result, AnalyzeEvent)
    assert ctx.data["evidence"] == {
        "similar_issues": [],
        "confluence": [],
        "specs": []
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
