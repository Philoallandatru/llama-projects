"""测试 IssueLoader"""

import pytest
from pathlib import Path
from src.core.issue_loader import IssueLoader


@pytest.mark.asyncio
async def test_load_issue_realtime():
    """测试实时加载单个 issue"""
    # 注意：需要配置真实的 Jira 环境变量才能运行
    loader = IssueLoader(
        server="https://jira.example.com",
        email="test@example.com",
        token="test_token"
    )

    # 这个测试需要真实的 Jira 环境
    # issue_data = await loader.load_issue_realtime("PROJ-123")
    # assert issue_data is not None
    # assert "key" in issue_data
    # assert "fields" in issue_data


@pytest.mark.asyncio
async def test_load_issues_batch():
    """测试批量加载 issues"""
    loader = IssueLoader(
        server="https://jira.example.com",
        email="test@example.com",
        token="test_token"
    )

    # 这个测试需要真实的 Jira 环境
    # issues = await loader.load_issues_batch(["PROJ-123", "PROJ-124"])
    # assert len(issues) == 2
