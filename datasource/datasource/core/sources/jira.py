"""Jira 数据源实现

支持从 Jira Server 抓取 Issues 和 Comments。
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any, Optional, List
from datetime import datetime

import aiohttp
import requests
from requests.auth import HTTPBasicAuth
from llama_index.core import Document
from atlassian import Jira

from .base import BaseDataSource
from ..utils.pagination import Paginator
from ..utils.retry import RetryHandler
from ..utils.async_http import AsyncHTTPClient
from ..metadata.field_extractor import JiraFieldExtractor

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
        self.email = config.options.get("email", "")  # email 可选，某些 Jira Server 不需要

        if not self.token:
            raise ValueError("Jira 数据源必须在 options 中指定 token")

        # 构建 JQL 查询
        self.jql = self._build_jql(config)

        # 配置选项
        self.max_results = config.options.get("max_results", 50)  # 每页结果数
        self.download_attachments = config.options.get("download_attachments", True)
        self.attachment_types = config.options.get("attachment_types", ["png", "jpg", "jpeg", "gif", "svg", "webp"])

        # 创建重试处理器
        self.retry_handler = RetryHandler(
            max_retries=config.options.get("max_retries", 3),
            base_delay=config.options.get("retry_delay", 5),
            backoff_strategy="exponential",
            handle_rate_limit=True
        )

        # 初始化字段提取器
        metadata_config = config.options.get("metadata_indexing", {})
        if metadata_config.get("enabled", True):
            field_config = metadata_config.get("indexed_fields", JiraFieldExtractor.get_default_config())
            self.field_extractor = JiraFieldExtractor(field_config)
        else:
            self.field_extractor = None

        # 配置要获取的字段
        self.fetch_fields = self._build_fetch_fields(metadata_config)

        # 使用 atlassian-python-api 创建 Jira 客户端
        self.jira_client = Jira(
            url=self.server,
            username=self.email,
            password=self.token,
            cloud=True  # Atlassian Cloud
        )

        logger.info(f"JiraDataSource initialized: server={self.server}, jql={self.jql}")

    def _build_fetch_fields(self, metadata_config: Dict) -> str:
        """构建 API 请求的 fields 参数

        Args:
            metadata_config: 元数据配置

        Returns:
            逗号分隔的字段列表
        """
        if not metadata_config.get("enabled", True):
            # 默认字段
            return "summary,description,status,priority,assignee,reporter,created,updated,comment"

        # 从配置中提取所有字段名
        field_names = set()

        # 元数据字段
        for field_config in metadata_config.get("indexed_fields", []):
            field_names.add(field_config['field'])

        # 全文检索字段
        for field in metadata_config.get("fulltext_fields", []):
            field_names.add(field.split('.')[0])  # 处理嵌套字段

        # 向量化字段
        for field in metadata_config.get("vector_fields", []):
            field_names.add(field)

        # 始终包含基础字段
        field_names.update(['summary', 'description', 'created', 'updated', 'comment'])

        return ','.join(field_names)

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

        # 提取并移除 ORDER BY 子句
        order_by = ""
        if base_jql:
            import re
            # 匹配 ORDER BY 及其后面的所有内容
            match = re.search(r'ORDER\s+BY\s+.+$', base_jql, re.IGNORECASE)
            if match:
                order_by = match.group(0).strip()
                # 移除 ORDER BY 部分，保留前面的条件
                base_jql = base_jql[:match.start()].strip()

        # 添加增量同步时间过滤
        if since:
            # 将 ISO 8601 格式转换为 Jira 格式 (YYYY-MM-DD HH:mm)
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                jira_time = dt.strftime('%Y-%m-%d %H:%M')

                time_filter = f"updated >= '{jira_time}'"

                if base_jql:
                    base_jql = f"{base_jql} AND {time_filter}"
                else:
                    base_jql = time_filter
            except ValueError:
                logger.warning(f"Invalid since timestamp: {since}, ignoring time filter")

        # 添加排序
        if not order_by:
            order_by = "ORDER BY updated DESC"

        if base_jql:
            return f"{base_jql} {order_by}"
        else:
            return order_by

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

        logger.info("=" * 60)
        logger.info("Starting Jira data fetch")
        logger.info(f"Server: {self.server}")
        logger.info(f"JQL: {jql}")
        logger.info(f"Since: {since or 'Full sync'}")
        logger.info("=" * 60)

        # 使用 atlassian-python-api 的 jql 方法获取所有 issues
        logger.info("Fetching issue list...")

        start_at = 0
        all_issues = []

        while True:
            # 使用 jql 方法分页获取
            result = self.jira_client.jql(
                jql=jql,
                start=start_at,
                limit=self.max_results,
                fields=self.fetch_fields
            )

            issues = result.get("issues", [])
            if not issues:
                break

            all_issues.extend(issues)

            # 检查是否还有更多数据
            total = result.get("total", 0)
            if start_at + len(issues) >= total:
                break

            start_at += len(issues)

        total_issues = len(all_issues)
        logger.info(f"Found {total_issues} issues to fetch")

        # 逐个获取详细信息
        for idx, issue in enumerate(all_issues, 1):
            issue_key = issue["key"]

            try:
                logger.info(f"[{idx}/{total_issues}] Fetching issue detail: {issue_key}")

                # 使用 atlassian-python-api 获取完整的 issue 数据
                full_issue = self.jira_client.issue(issue_key, fields="*all", expand="changelog,renderedFields")

                # 保存原始数据
                issue_file = output_dir / f"{self._sanitize_filename(issue_key)}.json"
                issue_file.write_text(
                    json.dumps(full_issue, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )

                summary = full_issue.get('fields', {}).get('summary', 'No summary')
                logger.info(f"[{idx}/{total_issues}] ✓ Saved: {issue_key} - {summary}")

                yield issue_key, full_issue

            except Exception as e:
                logger.error(f"[{idx}/{total_issues}] ✗ Failed to fetch issue {issue_key}: {e}")
                continue

        logger.info("=" * 60)
        logger.info(f"Jira fetch completed: {total_issues} issues")
        logger.info("=" * 60)

    def _fetch_issues_page(self, start_at: int, jql: Optional[str] = None) -> list:
        """获取一页 issues

        Args:
            start_at: 起始位置
            jql: JQL 查询语句（如果为 None，使用 self.jql）

        Returns:
            Issue 列表
        """
        url = f"{self.server}/rest/api/3/search"
        params = {
            "jql": jql if jql is not None else self.jql,
            "startAt": start_at,
            "maxResults": self.max_results,
            "fields": "summary,description,status,priority,assignee,reporter,created,updated"
        }

        response = self._request_with_retry("GET", url, params=params)
        data = response.json()

        return data.get("issues", [])


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

        # 提取元数据
        if self.field_extractor:
            metadata = self.field_extractor.extract(raw_data)
        else:
            # 回退到默认提取
            metadata = {
                "issue_key": item_id,
                "status": fields.get('status', {}).get('name', 'Unknown'),
                "priority": fields.get('priority', {}).get('name', 'Unknown'),
                "created": fields.get('created', 'Unknown'),
                "updated": fields.get('updated', 'Unknown'),
            }

        # 添加数据源信息
        metadata.update({
            "source_name": self.config.name,
            "source_type": "jira",
            "item_id": item_id,
            "has_attachments": len(attachment_paths) > 0,
            "attachment_count": len(attachment_paths),
            "attachment_paths": attachment_paths,
            "comment_count": len(comments)
        })

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

    # ==================== 异步抓取方法 ====================

    async def fetch_raw_async(
        self,
        output_dir: Path,
        since: Optional[str] = None,
        max_concurrent: int = 10
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """异步抓取 Jira Issues

        Args:
            output_dir: 原始数据保存目录
            since: 增量同步起始时间（ISO 8601 格式）
            max_concurrent: 最大并发请求数

        Returns:
            [(issue_key, raw_data), ...] 列表
        """
        # 构建 JQL（包含时间过滤）
        jql = self._build_jql(self.config, since)
        logger.info(f"Starting async Jira fetch with JQL: {jql}")

        # 创建异步 HTTP 客户端
        http_client = AsyncHTTPClient(
            max_concurrent=max_concurrent,
            max_retries=3,
            retry_delay=1.0,
            timeout=30
        )

        # 创建 aiohttp session（使用 BasicAuth）
        auth = aiohttp.BasicAuth(self.email, self.token)
        async with aiohttp.ClientSession(auth=auth) as session:
            # 1. 获取 issue 列表
            issue_keys = await self._fetch_issue_keys_async(
                session, http_client, jql
            )

            if not issue_keys:
                logger.info("No issues found")
                return []

            logger.info(f"Found {len(issue_keys)} issues, fetching details...")

            # 2. 并发获取每个 issue 的详细信息
            tasks = [
                self._fetch_issue_detail_async(session, http_client, issue_key)
                for issue_key in issue_keys
            ]

            results = await http_client.gather_with_concurrency(
                tasks, return_exceptions=True
            )

            # 3. 处理结果并保存
            fetched_issues = []
            for issue_key, result in zip(issue_keys, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to fetch issue {issue_key}: {result}")
                    continue

                try:
                    # 保存原始数据
                    issue_file = output_dir / f"{self._sanitize_filename(issue_key)}.json"
                    issue_file.write_text(
                        json.dumps(result, indent=2, ensure_ascii=False),
                        encoding="utf-8"
                    )

                    fetched_issues.append((issue_key, result))
                    logger.info(f"Fetched issue {issue_key} ({len(fetched_issues)}/{len(issue_keys)})")

                except Exception as e:
                    logger.error(f"Failed to save issue {issue_key}: {e}")
                    continue

            logger.info(f"Async Jira fetch completed: {len(fetched_issues)} issues")
            return fetched_issues

    async def _fetch_issue_keys_async(
        self,
        session: aiohttp.ClientSession,
        http_client: AsyncHTTPClient,
        jql: str
    ) -> List[str]:
        """异步获取所有 issue keys（分页）

        Args:
            session: aiohttp 会话
            http_client: 异步 HTTP 客户端
            jql: JQL 查询语句

        Returns:
            Issue key 列表
        """
        issue_keys = []
        start_at = 0

        while True:
            url = f"{self.server}/rest/api/3/search"
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": self.max_results,
                "fields": "key"  # 只获取 key，减少数据量
            }

            try:
                data = await http_client.get_json(session, url, params=params)
                issues = data.get("issues", [])

                if not issues:
                    break

                # 提取 issue keys
                for issue in issues:
                    issue_keys.append(issue["key"])

                # 检查是否还有更多数据
                total = data.get("total", 0)
                if start_at + len(issues) >= total:
                    break

                start_at += len(issues)

            except Exception as e:
                logger.error(f"Failed to fetch issue keys at offset {start_at}: {e}")
                break

        return issue_keys

    async def _fetch_issue_detail_async(
        self,
        session: aiohttp.ClientSession,
        http_client: AsyncHTTPClient,
        issue_key: str
    ) -> Dict[str, Any]:
        """异步获取 issue 详细信息（包含 comments）

        Args:
            session: aiohttp 会话
            http_client: 异步 HTTP 客户端
            issue_key: Issue key (如 PROJ-123)

        Returns:
            完整的 issue 数据
        """
        url = f"{self.server}/rest/api/3/issue/{issue_key}"
        params = {
            "expand": "renderedFields,names,schema,transitions,operations,changelog,comments"
        }

        return await http_client.get_json(session, url, params=params)

    def fetch_raw_sync_wrapper(
        self,
        output_dir: Path,
        since: Optional[str] = None,
        use_async: bool = True,
        max_concurrent: int = 10
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """同步包装器，支持选择同步或异步模式

        Args:
            output_dir: 原始数据保存目录
            since: 增量同步起始时间（ISO 8601 格式）
            use_async: 是否使用异步模式（默认 True）
            max_concurrent: 异步模式下的最大并发数

        Yields:
            (issue_key, raw_data) 元组
        """
        if use_async:
            # 使用异步模式
            results = asyncio.run(
                self.fetch_raw_async(output_dir, since, max_concurrent)
            )
            # 转换为 Iterator
            for item in results:
                yield item
        else:
            # 使用原有的同步模式
            yield from self.fetch_raw(output_dir, since)
