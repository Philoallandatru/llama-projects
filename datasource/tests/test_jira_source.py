"""测试 Jira 数据源"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
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
def mock_issue_response():
    """模拟 issue 响应"""
    return {
        "key": "TEST-123",
        "fields": {
            "summary": "Test Issue",
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


class TestJiraDataSource:
    """测试 Jira 数据源"""

    def test_init_with_valid_config(self, jira_config):
        """测试使用有效配置初始化"""
        source = JiraDataSource(jira_config)

        assert source.server == "https://jira.example.com"
        assert source.email == "test@example.com"
        assert source.token == "test_token"
        assert source.jql == "project = TEST ORDER BY updated DESC"

    def test_init_without_server(self):
        """测试缺少 server 参数"""
        config = SourceConfig(
            name="test",
            type=SourceType.JIRA,
            options={"email": "test@example.com", "token": "token"}
        )

        with pytest.raises(ValueError, match="必须指定 server"):
            JiraDataSource(config)

    def test_init_without_token(self):
        """测试缺少 token 参数"""
        config = SourceConfig(
            name="test",
            type=SourceType.JIRA,
            server="https://jira.example.com",
            options={"email": "test@example.com"}
        )

        with pytest.raises(ValueError, match="必须在 options 中指定 token"):
            JiraDataSource(config)

    def test_init_without_email(self):
        """测试不提供 email 参数（email 是可选的）"""
        config = SourceConfig(
            name="test",
            type=SourceType.JIRA,
            server="https://jira.example.com",
            options={"token": "token"}
        )

        # email 是可选的，不应该抛出错误
        source = JiraDataSource(config)
        assert source.email == ""
        assert source.token == "token"

    def test_build_jql_with_project(self, jira_config):
        """测试使用 project 构建 JQL"""
        source = JiraDataSource(jira_config)
        assert source.jql == "project = TEST ORDER BY updated DESC"

    def test_build_jql_with_custom_jql(self):
        """测试使用自定义 JQL"""
        config = SourceConfig(
            name="test",
            type=SourceType.JIRA,
            server="https://jira.example.com",
            jql="status = Open AND priority = High",
            options={"email": "test@example.com", "token": "token"}
        )

        source = JiraDataSource(config)
        assert source.jql == "status = Open AND priority = High ORDER BY updated DESC"

    @patch('datasource.core.sources.jira.requests.Session')
    def test_fetch_issues_page(self, mock_session, jira_config, mock_issue_response):
        """测试获取 issues 页面"""
        # 模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "issues": [mock_issue_response]
        }
        mock_response.status_code = 200
        mock_session.return_value.request.return_value = mock_response

        source = JiraDataSource(jira_config)
        issues = source._fetch_issues_page(0)

        assert len(issues) == 1
        assert issues[0]["key"] == "TEST-123"

    @patch('datasource.core.sources.jira.requests.Session')
    def test_fetch_issue_details(self, mock_session, jira_config, mock_issue_response):
        """测试获取 issue 详情"""
        # 模拟响应
        mock_response = Mock()
        mock_response.json.return_value = mock_issue_response
        mock_response.status_code = 200
        mock_session.return_value.request.return_value = mock_response

        source = JiraDataSource(jira_config)
        issue = source._fetch_issue_details("TEST-123")

        assert issue["key"] == "TEST-123"
        assert issue["fields"]["summary"] == "Test Issue"

    @patch('datasource.core.sources.jira.requests.Session')
    def test_request_with_retry_success(self, mock_session, jira_config):
        """测试请求重试成功"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_session.return_value.request.return_value = mock_response

        source = JiraDataSource(jira_config)
        response = source._request_with_retry("GET", "https://test.com")

        assert response.status_code == 200

    @patch('datasource.core.sources.jira.requests.Session')
    @patch('time.sleep')
    def test_request_with_retry_rate_limit(self, mock_sleep, mock_session, jira_config):
        """测试请求遇到限流"""
        # 第一次返回 429，第二次成功
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}

        mock_response_200 = Mock()
        mock_response_200.status_code = 200

        mock_session.return_value.request.side_effect = [
            mock_response_429,
            mock_response_200
        ]

        source = JiraDataSource(jira_config)
        response = source._request_with_retry("GET", "https://test.com")

        assert response.status_code == 200
        mock_sleep.assert_called_once_with(1)

    def test_build_document(self, jira_config, mock_issue_response, tmp_path):
        """测试构建 Document"""
        source = JiraDataSource(jira_config)
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()

        doc = source.build_document("TEST-123", mock_issue_response, assets_dir)

        # 验证 Document
        assert "TEST-123" in doc.text
        assert "Test Issue" in doc.text
        assert "Test description" in doc.text
        assert "Test comment" in doc.text

        # 验证元数据
        assert doc.metadata["item_id"] == "TEST-123"
        assert doc.metadata["issue_key"] == "TEST-123"
        assert doc.metadata["status"] == "Open"
        assert doc.metadata["priority"] == "High"
        assert doc.metadata["comment_count"] == 1

    def test_get_user_name(self, jira_config):
        """测试获取用户名"""
        source = JiraDataSource(jira_config)

        # 有用户
        user = {"displayName": "John Doe"}
        assert source._get_user_name(user) == "John Doe"

        # 无用户
        assert source._get_user_name(None) == "Unassigned"

        # 只有 name
        user = {"name": "jdoe"}
        assert source._get_user_name(user) == "jdoe"

    def test_sanitize_filename(self, jira_config):
        """测试文件名清理"""
        source = JiraDataSource(jira_config)

        # 包含不安全字符
        unsafe = "test<>:\"/\\|?*.txt"
        safe = source._sanitize_filename(unsafe)

        assert "<" not in safe
        assert ">" not in safe
        assert ":" not in safe
        assert "/" not in safe
        assert "\\" not in safe

    @patch('datasource.core.sources.jira.requests.Session')
    def test_fetch_raw(self, mock_session, jira_config, mock_issue_response, tmp_path):
        """测试完整的 fetch_raw 流程"""
        # 模拟搜索响应
        mock_search_response = Mock()
        mock_search_response.status_code = 200
        mock_search_response.json.return_value = {
            "issues": [{"key": "TEST-123"}]
        }

        # 模拟详情响应
        mock_detail_response = Mock()
        mock_detail_response.status_code = 200
        mock_detail_response.json.return_value = mock_issue_response

        mock_session.return_value.request.side_effect = [
            mock_search_response,
            mock_detail_response
        ]

        source = JiraDataSource(jira_config)
        output_dir = tmp_path / "raw"
        output_dir.mkdir()

        # 执行抓取
        results = list(source.fetch_raw(output_dir))

        # 验证结果
        assert len(results) == 1
        issue_key, raw_data = results[0]
        assert issue_key == "TEST-123"
        assert raw_data["key"] == "TEST-123"

        # 验证文件保存
        issue_file = output_dir / "TEST-123.json"
        assert issue_file.exists()
