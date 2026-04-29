"""性能对比：同步 vs 异步抓取

比较 Jira 和 Confluence 数据源的同步和异步抓取性能。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import time
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import shutil

from core.sources.jira import JiraDataSource
from core.sources.confluence import ConfluenceDataSource
from core.models import SourceConfig, SourceType


def create_mock_jira_data(count: int) -> Dict[str, Any]:
    """创建模拟的 Jira 数据"""
    return {
        "total": count,
        "issues": [{"key": f"TEST-{i}"} for i in range(count)]
    }


def create_mock_jira_issue(key: str) -> Dict[str, Any]:
    """创建模拟的 Jira issue"""
    return {
        "key": key,
        "fields": {
            "summary": f"Issue {key}",
            "description": "Test description",
            "status": {"name": "Open"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "John Doe"},
            "reporter": {"displayName": "Jane Smith"},
            "created": "2024-01-01T10:00:00.000+0000",
            "updated": "2024-01-02T10:00:00.000+0000",
            "comment": {"comments": []},
            "attachment": []
        }
    }


def create_mock_confluence_data(count: int) -> Dict[str, Any]:
    """创建模拟的 Confluence 数据"""
    return {
        "results": [{"id": str(i), "title": f"Page {i}"} for i in range(count)],
        "size": count
    }


def create_mock_confluence_page(page_id: str) -> Dict[str, Any]:
    """创建模拟的 Confluence 页面"""
    return {
        "id": page_id,
        "title": f"Page {page_id}",
        "type": "page",
        "status": "current",
        "body": {"storage": {"value": f"<p>Content for page {page_id}</p>"}},
        "version": {"number": 1},
        "space": {"key": "TEST", "name": "Test Space"}
    }


def benchmark_jira_sync(issue_count: int = 50) -> float:
    """基准测试：Jira 同步抓取"""
    config = SourceConfig(
        name="test_jira",
        type=SourceType.JIRA,
        server="https://jira.example.com",
        project="TEST",
        options={
            "email": "test@example.com",
            "token": "test_token",
            "max_results": 50
        }
    )

    source = JiraDataSource(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        with patch('core.sources.jira.requests.Session') as mock_session:
            # Mock 同步请求
            def mock_request(method, url, **kwargs):
                mock_response = Mock()
                mock_response.status_code = 200

                if "/search" in url:
                    mock_response.json.return_value = create_mock_jira_data(issue_count)
                elif "/issue/" in url:
                    issue_key = url.split("/")[-1].split("?")[0]
                    mock_response.json.return_value = create_mock_jira_issue(issue_key)
                    # 模拟网络延迟
                    time.sleep(0.01)

                return mock_response

            mock_session.return_value.request.side_effect = mock_request

            # 测量时间
            start_time = time.time()
            results = list(source.fetch_raw(output_dir))
            end_time = time.time()

            elapsed = end_time - start_time
            print(f"Jira 同步抓取 {issue_count} issues: {elapsed:.2f}s")
            return elapsed


def benchmark_jira_async(issue_count: int = 50, max_concurrent: int = 10) -> float:
    """基准测试：Jira 异步抓取"""
    config = SourceConfig(
        name="test_jira",
        type=SourceType.JIRA,
        server="https://jira.example.com",
        project="TEST",
        options={
            "email": "test@example.com",
            "token": "test_token",
            "max_results": 50
        }
    )

    source = JiraDataSource(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        with patch('core.sources.jira.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            # Mock 异步请求
            async def mock_get_json(session, url, **kwargs):
                if "/search" in url:
                    return create_mock_jira_data(issue_count)
                elif "/issue/" in url:
                    issue_key = url.split("/")[-1].split("?")[0]
                    # 模拟网络延迟
                    await asyncio.sleep(0.01)
                    return create_mock_jira_issue(issue_key)

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            async def mock_gather(tasks, **kwargs):
                return await asyncio.gather(*tasks, return_exceptions=True)

            mock_client.gather_with_concurrency = mock_gather
            mock_client_class.return_value = mock_client

            # 测量时间
            start_time = time.time()
            results = asyncio.run(source.fetch_raw_async(output_dir, max_concurrent=max_concurrent))
            end_time = time.time()

            elapsed = end_time - start_time
            print(f"Jira 异步抓取 {issue_count} issues (并发={max_concurrent}): {elapsed:.2f}s")
            return elapsed


def benchmark_confluence_sync(page_count: int = 50) -> float:
    """基准测试：Confluence 同步抓取"""
    config = SourceConfig(
        name="test_confluence",
        type=SourceType.CONFLUENCE,
        server="https://confluence.example.com",
        space="TEST",
        options={
            "email": "test@example.com",
            "token": "test_token"
        }
    )

    source = ConfluenceDataSource(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        with patch('core.sources.confluence.requests.Session') as mock_session:
            # Mock 同步请求
            def mock_request(method, url, **kwargs):
                mock_response = Mock()
                mock_response.status_code = 200

                params = kwargs.get("params", {})
                if "/content" in url and ("type" in params or "spaceKey" in params):
                    mock_response.json.return_value = create_mock_confluence_data(page_count)
                elif "/content/" in url:
                    page_id = url.split("/")[-1].split("?")[0]
                    mock_response.json.return_value = create_mock_confluence_page(page_id)
                    # 模拟网络延迟
                    time.sleep(0.01)
                else:
                    mock_response.json.return_value = {"results": [], "size": 0}

                return mock_response

            mock_session.return_value.request.side_effect = mock_request

            # 测量时间
            start_time = time.time()
            results = list(source.fetch_raw(output_dir))
            end_time = time.time()

            elapsed = end_time - start_time
            print(f"Confluence 同步抓取 {page_count} pages: {elapsed:.2f}s")
            return elapsed


def benchmark_confluence_async(page_count: int = 50, max_concurrent: int = 10) -> float:
    """基准测试：Confluence 异步抓取"""
    config = SourceConfig(
        name="test_confluence",
        type=SourceType.CONFLUENCE,
        server="https://confluence.example.com",
        space="TEST",
        options={
            "email": "test@example.com",
            "token": "test_token"
        }
    )

    source = ConfluenceDataSource(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        with patch('core.sources.confluence.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            # Mock 异步请求
            async def mock_get_json(session, url, **kwargs):
                params = kwargs.get("params", {})
                if "/content" in url and ("type" in params or "spaceKey" in params):
                    return create_mock_confluence_data(page_count)
                elif "/content/" in url:
                    page_id = url.split("/")[-1].split("?")[0]
                    # 模拟网络延迟
                    await asyncio.sleep(0.01)
                    return create_mock_confluence_page(page_id)
                return {"results": [], "size": 0}

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            async def mock_gather(tasks, **kwargs):
                return await asyncio.gather(*tasks, return_exceptions=True)

            mock_client.gather_with_concurrency = mock_gather
            mock_client_class.return_value = mock_client

            # 测量时间
            start_time = time.time()
            results = asyncio.run(source.fetch_raw_async(output_dir, max_concurrent=max_concurrent))
            end_time = time.time()

            elapsed = end_time - start_time
            print(f"Confluence 异步抓取 {page_count} pages (并发={max_concurrent}): {elapsed:.2f}s")
            return elapsed


def main():
    """运行性能对比"""
    print("=" * 60)
    print("数据源异步抓取性能对比")
    print("=" * 60)
    print()

    # 测试不同数量的数据
    test_counts = [10, 50, 100]
    concurrency_levels = [5, 10, 20]

    for count in test_counts:
        print(f"\n--- 测试数据量: {count} ---\n")

        # Jira 性能对比
        print("Jira 数据源:")
        sync_time = benchmark_jira_sync(count)

        for concurrency in concurrency_levels:
            async_time = benchmark_jira_async(count, concurrency)
            speedup = sync_time / async_time if async_time > 0 else 0
            print(f"  加速比 (并发={concurrency}): {speedup:.2f}x")

        print()

        # Confluence 性能对比
        print("Confluence 数据源:")
        sync_time = benchmark_confluence_sync(count)

        for concurrency in concurrency_levels:
            async_time = benchmark_confluence_async(count, concurrency)
            speedup = sync_time / async_time if async_time > 0 else 0
            print(f"  加速比 (并发={concurrency}): {speedup:.2f}x")

    print("\n" + "=" * 60)
    print("性能对比完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
