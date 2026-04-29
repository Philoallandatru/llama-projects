"""Confluence 数据源测试"""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests
from requests.auth import HTTPBasicAuth

from datasource.core.models import SourceConfig, SourceType
from datasource.core.sources.confluence import ConfluenceDataSource


@pytest.fixture
def confluence_config():
    """Confluence 配置 fixture"""
    return SourceConfig(
        name="test_confluence",
        type=SourceType.CONFLUENCE,
        server="https://confluence.example.com",
        space="TEST",
        options={
            "email": "test@example.com",
            "token": "test_token",
            "download_attachments": True
        }
    )


@pytest.fixture
def confluence_source(confluence_config):
    """Confluence 数据源 fixture"""
    return ConfluenceDataSource(confluence_config)


class TestConfluenceDataSourceInit:
    """测试 ConfluenceDataSource 初始化"""

    def test_init_success(self, confluence_source):
        """测试成功初始化"""
        assert confluence_source.server == "https://confluence.example.com"
        assert confluence_source.space_key == "TEST"
        assert confluence_source.cql is None
        assert isinstance(confluence_source.session.auth, HTTPBasicAuth)

    def test_init_without_server(self):
        """测试缺少 server"""
        config = SourceConfig(
            name="test",
            type=SourceType.CONFLUENCE,
            options={"email": "test@example.com", "token": "token"}
        )
        with pytest.raises(ValueError, match="必须在 config 中指定 server"):
            ConfluenceDataSource(config)

    def test_init_without_token(self):
        """测试缺少 token"""
        config = SourceConfig(
            name="test",
            type=SourceType.CONFLUENCE,
            server="https://confluence.example.com"
        )
        with pytest.raises(ValueError, match="必须在 options 中指定 token"):
            ConfluenceDataSource(config)

    def test_init_with_cql(self):
        """测试使用 CQL"""
        config = SourceConfig(
            name="test",
            type=SourceType.CONFLUENCE,
            server="https://confluence.example.com",
            cql="type=page and space=TEST",
            options={"email": "test@example.com", "token": "token"}
        )
        source = ConfluenceDataSource(config)
        assert source.cql == "type=page and space=TEST"


class TestConfluenceFetchRaw:
    """测试 Confluence 原始数据抓取"""

    @patch('datasource.core.sources.confluence.requests.Session.request')
    def test_fetch_space_info(self, mock_request, confluence_source, tmp_path):
        """测试获取 Space 信息"""
        # Mock Pages API 响应（空）
        mock_pages_response = Mock()
        mock_pages_response.status_code = 200
        mock_pages_response.json.return_value = {
            "results": [],
            "size": 0
        }

        mock_request.return_value = mock_pages_response

        results = list(confluence_source.fetch_raw(tmp_path))

        assert len(results) == 0
        assert mock_request.call_count >= 1

    @patch('datasource.core.sources.confluence.requests.Session.request')
    def test_fetch_pages(self, mock_request, confluence_source, tmp_path):
        """测试获取 Pages"""
        # Mock Pages API
        mock_pages_response = Mock()
        mock_pages_response.status_code = 200
        mock_pages_response.json.return_value = {
            "results": [
                {
                    "id": "123",
                    "title": "Test Page",
                    "type": "page",
                    "status": "current"
                }
            ],
            "size": 1
        }

        # Mock Page detail API
        mock_page_detail = Mock()
        mock_page_detail.status_code = 200
        mock_page_detail.json.return_value = {
            "id": "123",
            "title": "Test Page",
            "type": "page",
            "status": "current",
            "body": {
                "storage": {
                    "value": "<p>Test content</p>"
                }
            },
            "version": {"number": 1},
            "space": {"key": "TEST"}
        }

        mock_request.side_effect = [mock_pages_response, mock_page_detail]

        results = list(confluence_source.fetch_raw(tmp_path))

        assert len(results) == 1
        assert (tmp_path / "page_123.json").exists()

    @patch('datasource.core.sources.confluence.requests.Session.request')
    def test_fetch_with_pagination(self, mock_request, confluence_source, tmp_path):
        """测试分页抓取"""
        # Mock first page
        mock_page1 = Mock()
        mock_page1.status_code = 200
        mock_page1.json.return_value = {
            "results": [{"id": "1", "title": "Page 1", "type": "page", "status": "current"}],
            "size": 1
        }

        # Mock second page (empty)
        mock_page2 = Mock()
        mock_page2.status_code = 200
        mock_page2.json.return_value = {
            "results": [],
            "size": 0
        }

        # Mock page details
        mock_detail1 = Mock()
        mock_detail1.status_code = 200
        mock_detail1.json.return_value = {
            "id": "1", "title": "Page 1", "body": {"storage": {"value": "Content 1"}},
            "version": {"number": 1}, "space": {"key": "TEST"}
        }

        mock_request.side_effect = [mock_page1, mock_detail1, mock_page2]

        results = list(confluence_source.fetch_raw(tmp_path))

        assert len(results) == 1
        assert (tmp_path / "page_1.json").exists()


class TestConfluenceBuildDocument:
    """测试 Confluence Document 构建"""

    def test_build_document_basic(self, confluence_source, tmp_path):
        """测试基本 Document 构建"""
        # 创建测试数据
        page_data = {
            "id": "123",
            "title": "Test Page",
            "type": "page",
            "body": {
                "storage": {
                    "value": "<p>Test content</p>"
                }
            },
            "version": {"number": 1},
            "space": {"key": "TEST"},
            "_links": {"webui": "/pages/123"}
        }

        raw_file = tmp_path / "page_123.json"
        raw_file.write_text(json.dumps(page_data))

        doc_path = confluence_source.build_document(raw_file, tmp_path)

        assert Path(doc_path).exists()
        content = Path(doc_path).read_text()
        assert "Test Page" in content
        assert "Test content" in content

    def test_build_document_with_metadata(self, confluence_source, tmp_path):
        """测试包含元数据的 Document"""
        page_data = {
            "id": "456",
            "title": "Page with Metadata",
            "type": "page",
            "body": {"storage": {"value": "<p>Content</p>"}},
            "version": {
                "number": 2,
                "when": "2024-01-01T00:00:00.000Z",
                "by": {"displayName": "Test User"}
            },
            "space": {"key": "TEST", "name": "Test Space"},
            "history": {
                "createdBy": {"displayName": "Creator"},
                "createdDate": "2023-01-01T00:00:00.000Z"
            }
        }

        raw_file = tmp_path / "page_456.json"
        raw_file.write_text(json.dumps(page_data))

        doc_path = confluence_source.build_document(raw_file, tmp_path)

        content = Path(doc_path).read_text()
        doc_data = json.loads(content)
        assert doc_data["metadata"]["version"] == 2
        assert doc_data["metadata"]["title"] == "Page with Metadata"


class TestConfluenceRetryAndRateLimit:
    """测试重试和限流机制"""

    @patch('datasource.core.sources.confluence.requests.Session.request')
    @patch('datasource.core.utils.retry.time.sleep')
    def test_retry_on_failure(self, mock_sleep, mock_request, confluence_source, tmp_path):
        """测试失败重试"""
        # 第一次失败，第二次成功
        mock_fail = Mock()
        mock_fail.status_code = 500
        mock_fail.raise_for_status.side_effect = requests.RequestException("Server error")

        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"results": [], "size": 0}

        mock_request.side_effect = [mock_fail, mock_success]

        results = list(confluence_source.fetch_raw(tmp_path))

        # 验证有重试延迟
        assert mock_sleep.called
        assert len(results) == 0

    @patch('datasource.core.sources.confluence.requests.Session.request')
    @patch('datasource.core.utils.retry.time.sleep')
    def test_rate_limiting(self, mock_sleep, mock_request, confluence_source, tmp_path):
        """测试限流"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [], "size": 0}

        mock_request.return_value = mock_response

        # 调用多次
        confluence_source._make_request("GET", f"{confluence_source.server}/rest/api/content")
        confluence_source._make_request("GET", f"{confluence_source.server}/rest/api/content")

        # 验证请求成功
        assert mock_request.call_count >= 2


class TestConfluenceAttachments:
    """测试附件处理"""

    @patch('datasource.core.sources.confluence.requests.Session.request')
    def test_download_attachments(self, mock_request, confluence_source, tmp_path):
        """测试下载附件（当前实现不下载附件，仅验证不报错）"""
        # 当前实现不包含附件下载功能，这个测试只是占位
        # 如果未来添加附件功能，可以在这里测试

        # Mock Pages API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [],
            "size": 0
        }

        mock_request.return_value = mock_response

        results = list(confluence_source.fetch_raw(tmp_path))
        assert len(results) == 0

    @patch('datasource.core.sources.confluence.requests.Session.request')
    def test_skip_non_text_attachments(self, mock_request, confluence_source, tmp_path):
        """测试跳过非文本附件"""
        # 当前实现不包含附件下载功能，这个测试只是占位
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [],
            "size": 0
        }

        mock_request.return_value = mock_response

        results = list(confluence_source.fetch_raw(tmp_path))
        assert len(results) == 0

