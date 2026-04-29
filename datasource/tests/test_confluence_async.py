"""测试 Confluence 异步抓取功能"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import json

from datasource.core.sources.confluence import ConfluenceDataSource
from datasource.core.models import SourceConfig, SourceType


@pytest.fixture
def confluence_config():
    """创建 Confluence 配置"""
    return SourceConfig(
        name="test_confluence",
        type=SourceType.CONFLUENCE,
        server="https://confluence.example.com",
        space="TEST",
        options={
            "email": "test@example.com",
            "token": "test_token"
        }
    )


@pytest.fixture
def mock_page_list_response():
    """模拟页面列表响应"""
    return {
        "results": [
            {
                "id": "123",
                "title": "Test Page 1",
                "type": "page",
                "status": "current"
            },
            {
                "id": "124",
                "title": "Test Page 2",
                "type": "page",
                "status": "current"
            }
        ],
        "size": 2
    }


@pytest.fixture
def mock_page_detail_response():
    """模拟页面详情响应"""
    def create_page(page_id, title):
        return {
            "id": page_id,
            "title": title,
            "type": "page",
            "status": "current",
            "body": {
                "storage": {
                    "value": f"<p>Content for {title}</p>"
                }
            },
            "version": {"number": 1},
            "space": {"key": "TEST", "name": "Test Space"},
            "_links": {"webui": f"/pages/{page_id}"}
        }
    return create_page


class TestConfluenceAsyncFetch:
    """测试 Confluence 异步抓取"""

    @pytest.mark.asyncio
    async def test_fetch_pages_by_space_async(
        self,
        confluence_config,
        mock_page_list_response
    ):
        """测试按 Space 异步获取页面"""
        source = ConfluenceDataSource(confluence_config)

        mock_http_client = Mock()
        mock_http_client.get_json = AsyncMock(return_value=mock_page_list_response)

        mock_session = Mock()

        pages = await source._fetch_pages_by_space_async(
            mock_session,
            mock_http_client,
            "TEST"
        )

        assert len(pages) == 2
        assert pages[0]["id"] == "123"
        assert pages[1]["id"] == "124"

    @pytest.mark.asyncio
    async def test_fetch_pages_by_space_async_pagination(self, confluence_config):
        """测试按 Space 异步获取页面（分页）"""
        source = ConfluenceDataSource(confluence_config)

        # Mock 两页数据
        page1 = {
            "results": [{"id": "1", "title": "Page 1"}],
            "size": 1
        }
        page2 = {
            "results": [],
            "size": 0
        }

        mock_http_client = Mock()
        mock_http_client.get_json = AsyncMock(side_effect=[page1, page2])

        mock_session = Mock()

        pages = await source._fetch_pages_by_space_async(
            mock_session,
            mock_http_client,
            "TEST"
        )

        assert len(pages) == 1
        assert pages[0]["id"] == "1"

    @pytest.mark.asyncio
    async def test_fetch_pages_by_cql_async(
        self,
        confluence_config,
        mock_page_list_response
    ):
        """测试使用 CQL 异步获取页面"""
        source = ConfluenceDataSource(confluence_config)

        mock_http_client = Mock()
        mock_http_client.get_json = AsyncMock(return_value=mock_page_list_response)

        mock_session = Mock()

        pages = await source._fetch_pages_by_cql_async(
            mock_session,
            mock_http_client,
            "type=page and space=TEST"
        )

        assert len(pages) == 2

    @pytest.mark.asyncio
    async def test_fetch_page_detail_async(
        self,
        confluence_config,
        mock_page_detail_response
    ):
        """测试异步获取页面详情"""
        source = ConfluenceDataSource(confluence_config)

        page_data = mock_page_detail_response("123", "Test Page")

        mock_http_client = Mock()
        mock_http_client.get_json = AsyncMock(return_value=page_data)

        mock_session = Mock()

        result = await source._fetch_page_detail_async(
            mock_session,
            mock_http_client,
            "123"
        )

        assert result["id"] == "123"
        assert result["title"] == "Test Page"

    @pytest.mark.asyncio
    async def test_fetch_raw_async_full_flow(
        self,
        confluence_config,
        mock_page_list_response,
        mock_page_detail_response,
        tmp_path
    ):
        """测试完整的异步抓取流程"""
        source = ConfluenceDataSource(confluence_config)

        with patch('datasource.core.sources.confluence.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            # Mock get_json 调用
            async def mock_get_json(session, url, **kwargs):
                params = kwargs.get("params", {})
                # 匹配页面列表请求
                if "/content" in url and ("type" in params or "spaceKey" in params):
                    return mock_page_list_response
                # 匹配页面详情请求
                elif "/content/" in url:
                    page_id = url.split("/")[-1].split("?")[0]
                    title = f"Test Page {page_id}"
                    return mock_page_detail_response(page_id, title)
                # 默认返回空结果
                return {"results": [], "size": 0}

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
            assert results[0][0] == "123"
            assert results[1][0] == "124"

            # 验证文件保存
            assert (tmp_path / "page_123.json").exists()
            assert (tmp_path / "page_124.json").exists()

    def test_fetch_raw_sync_wrapper_async_mode(
        self,
        confluence_config,
        mock_page_list_response,
        mock_page_detail_response,
        tmp_path
    ):
        """测试同步包装器（异步模式）"""
        source = ConfluenceDataSource(confluence_config)

        with patch('datasource.core.sources.confluence.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            async def mock_get_json(session, url, **kwargs):
                params = kwargs.get("params", {})
                if "/content" in url and ("type" in params or "spaceKey" in params):
                    return mock_page_list_response
                elif "/content/" in url:
                    page_id = url.split("/")[-1].split("?")[0]
                    title = f"Test Page {page_id}"
                    return mock_page_detail_response(page_id, title)
                return {"results": [], "size": 0}

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

    @pytest.mark.asyncio
    async def test_fetch_raw_async_with_cql(
        self,
        mock_page_list_response,
        mock_page_detail_response,
        tmp_path
    ):
        """测试使用 CQL 的异步抓取"""
        config = SourceConfig(
            name="test_confluence",
            type=SourceType.CONFLUENCE,
            server="https://confluence.example.com",
            cql="type=page and label=important",
            options={
                "email": "test@example.com",
                "token": "test_token"
            }
        )
        source = ConfluenceDataSource(config)

        with patch('datasource.core.sources.confluence.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            async def mock_get_json(session, url, **kwargs):
                params = kwargs.get("params", {})
                # 验证使用了 CQL 搜索
                if "/search" in url or "cql" in params:
                    return mock_page_list_response
                elif "/content/" in url:
                    page_id = url.split("/")[-1].split("?")[0]
                    return mock_page_detail_response(page_id, f"Page {page_id}")
                return {"results": [], "size": 0}

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            async def mock_gather(tasks, **kwargs):
                return await asyncio.gather(*tasks, return_exceptions=True)

            mock_client.gather_with_concurrency = mock_gather
            mock_client_class.return_value = mock_client

            results = await source.fetch_raw_async(tmp_path)
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_fetch_raw_async_error_handling(self, confluence_config, tmp_path):
        """测试异步抓取的错误处理"""
        source = ConfluenceDataSource(confluence_config)

        with patch('datasource.core.sources.confluence.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            async def mock_get_json(session, url, **kwargs):
                params = kwargs.get("params", {})
                if "/content" in url and ("type" in params or "spaceKey" in params):
                    return {
                        "results": [{"id": "1"}, {"id": "2"}],
                        "size": 2
                    }
                return {"results": [], "size": 0}

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            # Mock gather 返回一个成功，一个异常
            async def mock_gather(tasks, **kwargs):
                return [
                    {"id": "1", "title": "Page 1", "body": {"storage": {"value": "Content"}}},
                    Exception("Network error")
                ]

            mock_client.gather_with_concurrency = mock_gather
            mock_client_class.return_value = mock_client

            # 执行抓取
            results = await source.fetch_raw_async(tmp_path)

            # 应该只有一个成功的结果
            assert len(results) == 1
            assert results[0][0] == "1"


class TestConfluenceAsyncPerformance:
    """测试 Confluence 异步性能"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, confluence_config, tmp_path):
        """测试并发请求"""
        source = ConfluenceDataSource(confluence_config)

        # 创建大量页面
        page_count = 20
        mock_page_list = {
            "results": [{"id": str(i), "title": f"Page {i}"} for i in range(page_count)],
            "size": page_count
        }

        with patch('datasource.core.sources.confluence.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            call_count = {"list": 0, "detail": 0}

            async def mock_get_json(session, url, **kwargs):
                params = kwargs.get("params", {})
                if "/content" in url and ("type" in params or "spaceKey" in params):
                    call_count["list"] += 1
                    return mock_page_list
                elif "/content/" in url:
                    call_count["detail"] += 1
                    page_id = url.split("/")[-1].split("?")[0]
                    return {
                        "id": page_id,
                        "title": f"Page {page_id}",
                        "body": {"storage": {"value": "Content"}}
                    }
                return {"results": [], "size": 0}

            mock_client.get_json = AsyncMock(side_effect=mock_get_json)

            async def mock_gather(tasks, **kwargs):
                return await asyncio.gather(*tasks, return_exceptions=True)

            mock_client.gather_with_concurrency = mock_gather
            mock_client_class.return_value = mock_client

            # 执行抓取
            results = await source.fetch_raw_async(tmp_path, max_concurrent=10)

            # 验证所有页面都被抓取
            assert len(results) == page_count

            # 验证并发调用
            assert call_count["detail"] == page_count

    @pytest.mark.asyncio
    async def test_fetch_raw_async_with_since(
        self,
        confluence_config,
        mock_page_list_response,
        mock_page_detail_response,
        tmp_path
    ):
        """测试带时间过滤的异步抓取"""
        source = ConfluenceDataSource(confluence_config)

        with patch('datasource.core.sources.confluence.AsyncHTTPClient') as mock_client_class:
            mock_client = Mock()

            async def mock_get_json(session, url, **kwargs):
                params = kwargs.get("params", {})
                if "/search" in url or "cql" in params:
                    # 验证包含时间过滤参数
                    return mock_page_list_response
                elif "/content" in url and ("type" in params or "spaceKey" in params):
                    return mock_page_list_response
                elif "/content/" in url:
                    page_id = url.split("/")[-1].split("?")[0]
                    return mock_page_detail_response(page_id, f"Page {page_id}")
                return {"results": [], "size": 0}

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
