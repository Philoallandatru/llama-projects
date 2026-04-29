"""Jira 数据源实现

支持从 Jira Server 抓取 Issues 和 Comments。
"""

import logging
import json
import time
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any, Optional
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth
from llama_index.core import Document

from .base import BaseDataSource
from ..utils.pagination import Paginator

logger = logging.getLogger(__name__)


class JiraDataSource(BaseDataSource):
    """Jira 数据源

    支持：
    - Jira Server API 认证（URL + Token）
    - JQL 查询
    - Issue 分页抓取
    - Comments 提取
    - 附件下载
    - 重试和限流
    """

    def __init__(self, config: "SourceConfig"):
        """初始化 Jira 数据源

        Args:
            config: 数据源配置，需要包含：
                - server: Jira Server URL
                - options.token: API Token
                - options.email: 用户邮箱（用于认证）
                - jql: JQL 查询语句（可选）
                - project: 项目 key（可选）
        """
        super().__init__(config)

        # 验证必需参数
        if not config.server:
            raise ValueError("Jira 数据源必须指定 server")

        self.server = config.server.rstrip('/')
        self.token = config.options.get("token")
        self.email = config.options.get("email")

        if not self.token:
            raise ValueError("Jira 数据源必须在 options 中指定 token")
        if not self.email:
            raise ValueError("Jira 数据源必须在 options 中指定 email")

        # 构建 JQL 查询
        self.jql = self._build_jql(config)

        # 配置选项
        self.max_results = config.options.get("max_results", 50)  # 每页结果数
        self.max_retries = config.options.get("max_retries", 3)
        self.retry_delay = config.options.get("retry_delay", 5)
        self.download_attachments = config.options.get("download_attachments", True)
        self.attachment_types = config.options.get("attachment_types", ["png", "jpg", "jpeg", "gif", "svg", "webp"])

        # 创建 session
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.email, self.token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        logger.info(f"JiraDataSource initialized: server={self.server}, jql={self.jql}")

    def _build_jql(self, config: "SourceConfig", since: Optional[str] = None) -> str:
        """构建 JQL 查询语句

        Args:
            config: 数据源配置
            since: 增量同步起始时间（ISO 8601 格式）

        Returns:
            JQL 查询字符串
        """
        # 基础 JQL
        base_jql = ""

        # 如果直接提供了 JQL，使用它
        if config.jql:
            base_jql = config.jql
        # 否则根据 project 构建
        elif config.project:
            base_jql = f"project = {config.project}"

        # 添加增量同步时间过滤
        if since:
            # 将 ISO 8601 格式转换为 Jira 格式 (YYYY-MM-DD HH:mm)
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                jira_time = dt.strftime('%Y-%m-%d %H:%M')

                time_filter = f"updated >= '{jira_time}'"

                if base_jql:
                    base_jql = f"({base_jql}) AND {time_filter}"
                else:
                    base_jql = time_filter
            except ValueError:
                logger.warning(f"Invalid since timestamp: {since}, ignoring time filter")

        # 添加排序
        if base_jql:
            return f"{base_jql} ORDER BY updated DESC"
        else:
            return "ORDER BY updated DESC"

    def fetch_raw(
        self,
        output_dir: Path,
        since: Optional[str] = None
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """抓取 Jira Issues

        Args:
            output_dir: 原始数据保存目录
            since: 增量同步起始时间（ISO 8601 格式）

        Yields:
            (issue_key, raw_data) 元组
        """
        # 构建 JQL（包含时间过滤）
        jql = self._build_jql(self.config, since)
        logger.info(f"Starting Jira fetch with JQL: {jql}")

        # 使用分页器获取所有 issue 列表
        def fetch_func(start: int, limit: int) -> Dict[str, Any]:
            url = f"{self.server}/rest/api/2/search"
            params = {
                "jql": jql,
                "startAt": start,
                "maxResults": limit,
                "fields": "summary,description,status,priority,assignee,reporter,created,updated"
            }
            response = self._request_with_retry("GET", url, params=params)
            return response.json()

        issues = Paginator.paginate(
            fetch_func,
            page_size=self.max_results,
            results_key="issues",
            size_key="maxResults"  # Jira 返回的是 maxResults 而不是实际大小
        )

        # 逐个获取详细信息
        total_fetched = 0
        for issue in issues:
            issue_key = issue["key"]

            try:
                # 获取完整的 issue 数据（包含 comments）
                full_issue = self._fetch_issue_details(issue_key)

                # 保存原始数据
                issue_file = output_dir / f"{self._sanitize_filename(issue_key)}.json"
                issue_file.write_text(
                    json.dumps(full_issue, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )

                total_fetched += 1
                logger.info(f"Fetched issue {issue_key} ({total_fetched})")

                yield issue_key, full_issue

            except Exception as e:
                logger.error(f"Failed to fetch issue {issue_key}: {e}")
                continue

        logger.info(f"Jira fetch completed: {total_fetched} issues")

    def _fetch_issues_page(self, start_at: int, jql: Optional[str] = None) -> list:
        """获取一页 issues

        Args:
            start_at: 起始位置
            jql: JQL 查询语句（如果为 None，使用 self.jql）

        Returns:
            Issue 列表
        """
        url = f"{self.server}/rest/api/2/search"
        params = {
            "jql": jql if jql is not None else self.jql,
            "startAt": start_at,
            "maxResults": self.max_results,
            "fields": "summary,description,status,priority,assignee,reporter,created,updated"
        }

        response = self._request_with_retry("GET", url, params=params)
        data = response.json()

        return data.get("issues", [])

    def _fetch_issue_details(self, issue_key: str) -> Dict[str, Any]:
        """获取 issue 详细信息（包含 comments）

        Args:
            issue_key: Issue key (如 PROJ-123)

        Returns:
            完整的 issue 数据
        """
        url = f"{self.server}/rest/api/2/issue/{issue_key}"
        params = {
            "expand": "renderedFields,names,schema,transitions,operations,changelog,comments"
        }

        response = self._request_with_retry("GET", url, params=params)
        return response.json()

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """带重试的 HTTP 请求

        Args:
            method: HTTP 方法
            url: 请求 URL
            **kwargs: 其他请求参数

        Returns:
            Response 对象

        Raises:
            requests.RequestException: 请求失败
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)

                # 处理 429 限流
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                    logger.warning(f"Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                # 检查其他错误
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise

    def build_document(
        self,
        item_id: str,
        raw_data: Dict[str, Any],
        assets_dir: Path
    ) -> Document:
        """将 Jira Issue 转换为 LlamaIndex Document

        Args:
            item_id: Issue key
            raw_data: 原始 issue 数据
            assets_dir: 附件保存目录

        Returns:
            LlamaIndex Document
        """
        fields = raw_data.get("fields", {})

        # 使用 HTMLCleaner 清理 HTML 内容
        from datasource.core.utils.html_cleaner import HTMLCleaner

        # 清理 description
        description = fields.get('description', 'No description')
        if HTMLCleaner.has_html_tags(description):
            description = HTMLCleaner.clean(description, preserve_links=True, preserve_formatting=True)

        # 构建 Markdown 内容
        content_parts = [
            f"# {item_id}: {fields.get('summary', 'No Summary')}",
            "",
            "## Details",
            f"- **Status**: {fields.get('status', {}).get('name', 'Unknown')}",
            f"- **Priority**: {fields.get('priority', {}).get('name', 'Unknown')}",
            f"- **Assignee**: {self._get_user_name(fields.get('assignee'))}",
            f"- **Reporter**: {self._get_user_name(fields.get('reporter'))}",
            f"- **Created**: {fields.get('created', 'Unknown')}",
            f"- **Updated**: {fields.get('updated', 'Unknown')}",
            "",
            "## Description",
            description,
            ""
        ]

        # 添加 Comments
        comments = raw_data.get("fields", {}).get("comment", {}).get("comments", [])
        if comments:
            content_parts.append("## Comments")
            content_parts.append("")
            for comment in comments:
                author = self._get_user_name(comment.get("author"))
                created = comment.get("created", "Unknown")
                body = comment.get("body", "")

                # 清理 comment body 中的 HTML
                if HTMLCleaner.has_html_tags(body):
                    body = HTMLCleaner.clean(body, preserve_links=True, preserve_formatting=True)

                content_parts.append(f"### {author} - {created}")
                content_parts.append(body)
                content_parts.append("")

        # 下载附件（如果启用）
        attachment_paths = []
        if self.download_attachments:
            attachments = fields.get("attachment", [])
            for attachment in attachments:
                filename = attachment.get("filename", "")
                ext = filename.split(".")[-1].lower() if "." in filename else ""

                if ext in self.attachment_types:
                    try:
                        path = self._download_attachment(attachment, assets_dir)
                        if path:
                            attachment_paths.append(str(path))
                    except Exception as e:
                        logger.warning(f"Failed to download attachment {filename}: {e}")

        # 构建元数据
        metadata = {
            "source_name": self.config.name,
            "source_type": "jira",
            "item_id": item_id,
            "issue_key": item_id,
            "status": fields.get('status', {}).get('name', 'Unknown'),
            "priority": fields.get('priority', {}).get('name', 'Unknown'),
            "created": fields.get('created', 'Unknown'),
            "updated": fields.get('updated', 'Unknown'),
            "has_attachments": len(attachment_paths) > 0,
            "attachment_count": len(attachment_paths),
            "attachment_paths": attachment_paths,
            "comment_count": len(comments)
        }

        # 创建 Document
        text = "\n".join(content_parts)
        return Document(text=text, metadata=metadata)

    def _get_user_name(self, user: Optional[Dict[str, Any]]) -> str:
        """获取用户名

        Args:
            user: 用户对象

        Returns:
            用户名或 "Unassigned"
        """
        if not user:
            return "Unassigned"
        return user.get("displayName", user.get("name", "Unknown"))

    def _download_attachment(
        self,
        attachment: Dict[str, Any],
        assets_dir: Path
    ) -> Optional[Path]:
        """下载附件

        Args:
            attachment: 附件对象
            assets_dir: 附件保存目录

        Returns:
            附件保存路径或 None
        """
        url = attachment.get("content")
        filename = attachment.get("filename")

        if not url or not filename:
            return None

        # 创建保存路径
        safe_filename = self._sanitize_filename(filename)
        save_path = assets_dir / safe_filename

        # 下载文件
        try:
            response = self._request_with_retry("GET", url, stream=True)

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded attachment: {filename}")
            return save_path

        except Exception as e:
            logger.error(f"Failed to download attachment {filename}: {e}")
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名

        Args:
            filename: 原始文件名

        Returns:
            安全的文件名
        """
        # 替换不安全字符
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        return filename
