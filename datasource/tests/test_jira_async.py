"""测试 Jira 异步抓取功能"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import json

from datasource.core.sources.jira import JiraDataSource
from datasource.core.models import SourceConfig, SourceType


@pytest.fixture
def jira_config():
    """创建 Jira 配置"""
    return SourceConfig(
        name="test_jira",
        type=SourceType.JIRA,
        server="https://jira.example.com",
        project="TEST",
        options={
            "email": "test@example.com",
            "token": "test_token",
            "max_results": 2
        }
    )


@pytest.fixture
def mock_issue_list_response():
    """模拟 issue 列表响应"""
    return {
        "total": 2,
        "issues": [
            {"key": "TEST-123"},
            {"key": "TEST-124"}
        ]
    }


@pytest.fixture
def mock_issue_detail_response():
    """模拟 issue 详情响应"""
    def create_issue(key):
        return {
            "key": key,
            "fields": {
                "summary": f"Test Issue {key}",
                "description": "Test description",
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "assignee": {"displayName": "John Doe"},
                "reporter": {"displayName": "Jane Smith"},
                "created": "2024-01-01T10:00:00.000+0000",
                "updated": "2024-01-02T10:00:00.000+0000",
                "comment": {
                    "comments": [
                        {
                            "author": {"displayName": "Bob"},
                            "created": "2024-01-01T11:00:00.000+0000",
                            "body": "Test comment"
                        }
                    ]
                },
                "attachment": []
            }
        }
    return create_issue


class TestJiraAsyncFetch:
    """测试 Jira 异步抓取"""

    @pytest.mark.asyncio
    async def test_fetch_issue_keys_async(self, jira_config, mock_issue_list_response):
        """测试异步获取 issue keys"""
        source = JiraDataSource(jira_config)

        # Mock AsyncHTTPClient.get_json
        mock_http_client = Mock()
        mock_http_client.get_json = AsyncMock(return_value=mock_issue_list_response)

        mock_session = Mock()

        keys = await source._fetch_issue_keys_async(
            mock_session,
            mock_http_client,
            "project = TEST"
        )

        assert len(keys) == 2
        assert "TEST-123" in keys
        assert "TEST-124" in keys

    @pytest.mark.asyncio
    async def test_fetch_issue_keys_async_pagination(self, jira_config):
        """测试异步获取 issue keys（分页）"""
        source = JiraDataSource(jira_config)

        # Mock 两页数据
        page1 = {
            "total": 3,
            "issues": [{"key": "TEST-1"}, {"key": "TEST-2"}]
        }
        page2 = {
            "total": 3,
            "issues": [{"key": "TEST-3"}]
        }

        mock_http_client = Mock()
        mock_http_client.get_json = AsyncMock(side_effect=[page1, page2])

        mock_session = Mock()

        keys = await source._fetch_issue_keys_async(
            mock_session,
            mock_http_client,
            "project = TEST"
        )

        assert len(keys) == 3
        assert keys == ["TEST-1", "TEST-2", "TEST-3"]

    @pytest.mark.asyncio
    async def test_fetch_issue_detail_async(self, jira_config, mock_issue_detail_response):
        """测试异步获取 issue 详情"""
        source = JiraDataSource(jira_config)

        issue_data = mock_issue_detail_response("TEST-123")

        mock_http_client = Mock()
        mock_http_client.get_json = AsyncMock(return_value=issue_data)

        mock_session = Mock()

        result = await source._fetch_issue_detail_async(
            mock_session,
            mock_http_client,
            "TEST-123"
        )

        assert result["key"] == "TEST-123"
        assert result["fields"]["summary"] == "Test Issue TEST-123"

    @pytest.mark.asyncio
    async def test_fetch_raw_async_full_flow(
        self,
        jira_config,
        mock_issue_list_response,
        mock_issue_detail_response,
        tmp_path
    ):
        """测试完整的异步抓取流程"""
        source = JiraDataSource(jira_config)

        # Mock AsyncHTTPClient
        with patch('datasource.core.sources.jira.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            # Mock get_json 调用
            async def mock_get_json(session, url, **kwargs):
                if "/search" in url:
                    return mock_issue_list_response
                elif "/issue/" in url:
                    issue_key = url.split("/")[-1].split("?")[0]
                    return mock_issue_detail_response(issue_key)

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            # Mock gather_with_concurrency
            async def mock_gather(tasks, **kwargs):
                return await asyncio.gather(*tasks, return_exceptions=True)

            mock_client.gather_with_concurrency = mock_gather

            mock_client_class.return_value = mock_client

            # 执行异步抓取
            results = await source.fetch_raw_async(tmp_path)

            # 验证结果
            assert len(results) == 2
            assert results[0][0] == "TEST-123"
            assert results[1][0] == "TEST-124"

            # 验证文件保存
            assert (tmp_path / "TEST-123.json").exists()
            assert (tmp_path / "TEST-124.json").exists()

            # 验证文件内容
            with open(tmp_path / "TEST-123.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data["key"] == "TEST-123"

    def test_fetch_raw_sync_wrapper_async_mode(
        self,
        jira_config,
        mock_issue_list_response,
        mock_issue_detail_response,
        tmp_path
    ):
        """测试同步包装器（异步模式）"""
        source = JiraDataSource(jira_config)

        with patch('datasource.core.sources.jira.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            async def mock_get_json(session, url, **kwargs):
                if "/search" in url:
                    return mock_issue_list_response
                elif "/issue/" in url:
                    issue_key = url.split("/")[-1].split("?")[0]
                    return mock_issue_detail_response(issue_key)

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            async def mock_gather(tasks, **kwargs):
                return await asyncio.gather(*tasks, return_exceptions=True)

            mock_client.gather_with_concurrency = mock_gather
            mock_client_class.return_value = mock_client

            # 使用异步模式
            results = list(source.fetch_raw_sync_wrapper(
                tmp_path,
                use_async=True,
                max_concurrent=5
            ))

            assert len(results) == 2
            assert results[0][0] == "TEST-123"
            assert results[1][0] == "TEST-124"

    @patch('datasource.core.sources.jira.requests.Session')
    def test_fetch_raw_sync_wrapper_sync_mode(
        self,
        mock_session,
        jira_config,
        mock_issue_list_response,
        mock_issue_detail_response,
        tmp_path
    ):
        """测试同步包装器（同步模式）"""
        # Mock 同步请求
        def mock_request(method, url, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200

            if "/search" in url:
                mock_response.json.return_value = mock_issue_list_response
            elif "/issue/" in url:
                issue_key = url.split("/")[-1].split("?")[0]
                mock_response.json.return_value = mock_issue_detail_response(issue_key)

            return mock_response

        mock_session.return_value.request.side_effect = mock_request

        source = JiraDataSource(jira_config)

        # 使用同步模式
        results = list(source.fetch_raw_sync_wrapper(
            tmp_path,
            use_async=False
        ))

        assert len(results) == 2
        assert results[0][0] == "TEST-123"
        assert results[1][0] == "TEST-124"

    @pytest.mark.asyncio
    async def test_fetch_raw_async_with_since(
        self,
        jira_config,
        mock_issue_list_response,
        mock_issue_detail_response,
        tmp_path
    ):
        """测试带时间过滤的异步抓取"""
        source = JiraDataSource(jira_config)

        with patch('datasource.core.sources.jira.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            async def mock_get_json(session, url, **kwargs):
                # 验证 JQL 包含时间过滤
                if "/search" in url:
                    params = kwargs.get("params", {})
                    jql = params.get("jql", "")
                    assert "updated >=" in jql
                    return mock_issue_list_response
                elif "/issue/" in url:
                    issue_key = url.split("/")[-1].split("?")[0]
                    return mock_issue_detail_response(issue_key)

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            async def mock_gather(tasks, **kwargs):
                return await asyncio.gather(*tasks, return_exceptions=True)

            mock_client.gather_with_concurrency = mock_gather
            mock_client_class.return_value = mock_client

            # 执行带时间过滤的抓取
            results = await source.fetch_raw_async(
                tmp_path,
                since="2024-01-01T00:00:00Z"
            )

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_fetch_raw_async_error_handling(self, jira_config, tmp_path):
        """测试异步抓取的错误处理"""
        source = JiraDataSource(jira_config)

        with patch('datasource.core.sources.jira.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            # Mock 一个成功，一个失败
            async def mock_get_json(session, url, **kwargs):
                if "/search" in url:
                    return {
                        "total": 2,
                        "issues": [{"key": "TEST-1"}, {"key": "TEST-2"}]
                    }

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            # Mock gather 返回一个成功，一个异常
            async def mock_gather(tasks, **kwargs):
                return [
                    {"key": "TEST-1", "fields": {}},
                    Exception("Network error")
                ]

            mock_client.gather_with_concurrency = mock_gather
            mock_client_class.return_value = mock_client

            # 执行抓取
            results = await source.fetch_raw_async(tmp_path)

            # 应该只有一个成功的结果
            assert len(results) == 1
            assert results[0][0] == "TEST-1"


class TestJiraAsyncPerformance:
    """测试 Jira 异步性能"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, jira_config, tmp_path):
        """测试并发请求"""
        source = JiraDataSource(jira_config)

        # 创建大量 issues
        issue_count = 20
        mock_issue_list = {
            "total": issue_count,
            "issues": [{"key": f"TEST-{i}"} for i in range(issue_count)]
        }

        with patch('datasource.core.sources.jira.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            call_count = {"search": 0, "detail": 0}

            async def mock_get_json(session, url, **kwargs):
                if "/search" in url:
                    call_count["search"] += 1
                    return mock_issue_list
                elif "/issue/" in url:
                    call_count["detail"] += 1
                    issue_key = url.split("/")[-1].split("?")[0]
                    return {"key": issue_key, "fields": {}}

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            async def mock_gather(tasks, **kwargs):
                return await asyncio.gather(*tasks, return_exceptions=True)

            mock_client.gather_with_concurrency = mock_gather
            mock_client_class.return_value = mock_client

            # 执行抓取
            results = await source.fetch_raw_async(tmp_path, max_concurrent=10)

            # 验证所有 issues 都被抓取
            assert len(results) == issue_count

            # 验证并发调用
            assert call_count["detail"] == issue_count
