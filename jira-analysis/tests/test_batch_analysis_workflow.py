"""Batch Analysis Workflow 测试"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.workflows.batch_analysis import (
    BatchAnalysisWorkflow,
    LoadBatchEvent,
    AnalyzeBatchEvent,
    GenerateReportEvent
)


@pytest.fixture
def mock_jira_config():
    return {
        "server": "https://jira.example.com",
        "email": "test@example.com",
        "token": "test_token"
    }


@pytest.fixture
def mock_llm_config():
    return {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:14b",
        "temperature": 0.1,
        "max_tokens": 4096
    }


@pytest.fixture
def mock_issues_data():
    return [
        {
            "key": "TEST-123",
            "fields": {
                "summary": "Test issue 1",
                "description": "Description 1",
                "issuetype": {"name": "Bug"},
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "created": "2024-01-01T00:00:00.000+0000",
                "updated": "2024-01-02T00:00:00.000+0000",
                "comment": {"comments": []}
            }
        },
        {
            "key": "TEST-124",
            "fields": {
                "summary": "Test issue 2",
                "description": "Description 2",
                "issuetype": {"name": "Task"},
                "status": {"name": "In Progress"},
                "priority": {"name": "Medium"},
                "created": "2024-01-01T00:00:00.000+0000",
                "updated": "2024-01-02T00:00:00.000+0000",
                "comment": {"comments": []}
            }
        }
    ]


@pytest.mark.asyncio
async def test_workflow_initialization(mock_jira_config, mock_llm_config, tmp_path):
    workflow = BatchAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path,
        max_concurrent=3
    )
    
    assert workflow.jira_config == mock_jira_config
    assert workflow.llm_config == mock_llm_config
    assert workflow.max_concurrent == 3


@pytest.mark.asyncio
async def test_start_step(mock_jira_config, mock_llm_config, tmp_path):
    workflow = BatchAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path
    )
    
    ctx = MagicMock()
    ctx.data = {}
    
    from llama_index.core.workflow import StartEvent
    ev = StartEvent(issue_keys=["TEST-123", "TEST-124"], mode="balanced")
    
    result = await workflow.start(ctx, ev)
    
    assert isinstance(result, LoadBatchEvent)
    assert result.issue_keys == ["TEST-123", "TEST-124"]
    assert ctx.data["mode"] == "balanced"


@pytest.mark.asyncio
async def test_start_step_missing_issue_keys(mock_jira_config, mock_llm_config, tmp_path):
    workflow = BatchAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path
    )
    
    ctx = MagicMock()
    ctx.data = {}
    
    from llama_index.core.workflow import StartEvent
    ev = StartEvent()
    
    with pytest.raises(ValueError, match="issue_keys is required"):
        await workflow.start(ctx, ev)


@pytest.mark.asyncio
async def test_load_batch_step(mock_jira_config, mock_llm_config, mock_issues_data, tmp_path):
    workflow = BatchAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path
    )
    
    ctx = MagicMock()
    ctx.data = {}
    ctx.write_event_to_stream = MagicMock()
    
    with patch('src.workflows.batch_analysis.IssueLoader') as MockLoader:
        mock_loader = MockLoader.return_value
        mock_loader.load_issues_batch = AsyncMock(return_value=mock_issues_data)
        
        ev = LoadBatchEvent(issue_keys=["TEST-123", "TEST-124"])
        result = await workflow.load_batch(ctx, ev)
        
        assert isinstance(result, AnalyzeBatchEvent)
        assert ctx.data["issues_data"] == mock_issues_data


@pytest.mark.asyncio
async def test_generate_report_step(mock_jira_config, mock_llm_config, tmp_path):
    workflow = BatchAnalysisWorkflow(
        jira_config=mock_jira_config,
        llm_config=mock_llm_config,
        index_base_path=tmp_path,
        profiles_dir=tmp_path
    )
    
    ctx = MagicMock()
    ctx.data = {
        "results": [
            {"issue_key": "TEST-123", "profile": "rca", "status": "success"},
            {"issue_key": "TEST-124", "profile": "general", "status": "success"}
        ],
        "generate_summary": False
    }
    ctx.write_event_to_stream = MagicMock()
    
    from llama_index.core.workflow import StopEvent
    ev = GenerateReportEvent()
    result = await workflow.generate_report(ctx, ev)
    
    assert isinstance(result, StopEvent)
    assert result.result["total"] == 2
    assert result.result["success"] == 2
    assert result.result["failed"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
