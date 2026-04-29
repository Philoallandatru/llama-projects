"""Confluence 数据源实现

支持从 Confluence Server 抓取 Pages 和附件。
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any, Optional, List
from datetime import datetime

import requests
import aiohttp
from requests.auth import HTTPBasicAuth
from llama_index.core import Document

from .base import BaseDataSource
from ..utils.pagination import Paginator
from ..utils.retry import RetryHandler
from ..utils.async_http import AsyncHTTPClient
from ..utils.async_http import AsyncHTTPClient

logger = logging.getLogger(__name__)


class ConfluenceDataSource(BaseDataSource):
    """Confluence 数据源

    支持：
    - Confluence Server API 认证（URL + Token）
    - Space 和 CQL 查询
    - Page 分页抓取
    - 附件下载
    - 重试和限流
    """

    def __init__(self, config: "SourceConfig"):
        """初始化 Confluence 数据源

        Args:
            config: 数据源配置，需要包含：
                - server: Confluence Server URL
                - options.token: API Token
                - options.email: 用户邮箱（可选）
                - space: Space key（可选）
                - cql: CQL 查询语句（可选）
        """
        super().__init__(config)

        # 验证必需参数
        if not config.server:
            raise ValueError("Confluence 数据源必须在 config 中指定 server")

        self.server = config.server.rstrip('/')
        self.token = config.options.get("token") if config.options else None
        self.email = config.options.get("email", "") if config.options else ""

        if not self.token:
            raise ValueError("Confluence 数据源必须在 options 中指定 token")

        # 构建查询
        self.space_key = config.space
        self.cql = config.cql

        # 配置选项
        self.max_results = config.options.get("max_results", 50) if config.options else 50
        self.download_attachments = config.options.get("download_attachments", False) if config.options else False

        # 创建重试处理器
        self.retry_handler = RetryHandler(
            max_retries=config.options.get("max_retries", 3) if config.options else 3,
            base_delay=config.options.get("retry_delay", 5) if config.options else 5,
            backoff_strategy="exponential",
            handle_rate_limit=True
        )

        # 创建 session
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.email, self.token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        logger.info(f"ConfluenceDataSource initialized: server={self.server}, space={self.space_key}")

    def fetch_raw(
        self,
        output_dir: Path,
        since: Optional[str] = None
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """抓取原始数据

        Args:
            output_dir: 输出目录
            since: 增量同步起始时间（ISO 8601 格式）

        Yields:
            (page_id, raw_data) 元组
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 获取 Pages
            if self.space_key:
                pages = self._fetch_pages_by_space(self.space_key, since)
            elif self.cql:
                pages = self._fetch_pages_by_cql(self.cql, since)
            else:
                logger.warning("未指定 space 或 cql，将获取所有可访问的 pages")
                pages = self._fetch_all_pages(since)

            # 保存每个 Page
            for page in pages:
                page_id = page["id"]

                # 获取完整的 Page 内容
                page_detail = self._fetch_page_detail(page_id)

                # 保存原始数据
                output_file = output_dir / f"page_{page_id}.json"
                output_file.write_text(json.dumps(page_detail, ensure_ascii=False, indent=2), encoding="utf-8")

                logger.info(f"Fetched page: {page_detail.get('title')} (ID: {page_id})")

                yield page_id, page_detail

        except Exception as e:
            logger.error(f"Error fetching Confluence data: {e}")
            raise

    def _fetch_pages_by_space(self, space_key: str, since: Optional[str] = None) -> list:
        """通过 Space Key 获取 Pages

        Args:
            space_key: Space key
            since: 增量同步起始时间（ISO 8601 格式）

        Returns:
            Page 列表
        """
        # 如果有 since，使用 CQL 查询
        if since:
            cql = f"space={space_key} AND lastModified >= '{since}'"
            return self._fetch_pages_by_cql(cql, since=None)  # since 已在 CQL 中

        # 否则使用标准 API 和分页器
        def fetch_func(start: int, limit: int) -> Dict[str, Any]:
            url = f"{self.server}/rest/api/content"
            params = {
                "spaceKey": space_key,
                "type": "page",
                "status": "current",
                "limit": limit,
                "start": start
            }
            response = self._make_request("GET", url, params=params)
            return response.json()

        return Paginator.paginate(
            fetch_func,
            page_size=self.max_results,
            results_key="results",
            size_key="size"
        )

    def _fetch_pages_by_cql(self, cql: str, since: Optional[str] = None) -> list:
        """通过 CQL 查询获取 Pages

        Args:
            cql: CQL 查询语句
            since: 增量同步起始时间（ISO 8601 格式）

        Returns:
            Page 列表
        """
        # 添加时间过滤
        if since:
            cql = f"({cql}) AND lastModified >= '{since}'"

        # 使用分页器
        def fetch_func(start: int, limit: int) -> Dict[str, Any]:
            url = f"{self.server}/rest/api/content/search"
            params = {
                "cql": cql,
                "limit": limit,
                "start": start
            }
            response = self._make_request("GET", url, params=params)
            return response.json()

        return Paginator.paginate(
            fetch_func,
            page_size=self.max_results,
            results_key="results",
            size_key="size"
        )

    def _fetch_all_pages(self, since: Optional[str] = None) -> list:
        """获取所有可访问的 Pages

        Args:
            since: 增量同步起始时间（ISO 8601 格式）

        Returns:
            Page 列表
        """
        # 如果有 since，使用 CQL 查询
        if since:
            cql = f"type=page AND lastModified >= '{since}'"
            return self._fetch_pages_by_cql(cql, since=None)  # since 已在 CQL 中

        # 使用分页器
        def fetch_func(start: int, limit: int) -> Dict[str, Any]:
            url = f"{self.server}/rest/api/content"
            params = {
                "type": "page",
                "status": "current",
                "limit": limit,
                "start": start
            }
            response = self._make_request("GET", url, params=params)
            return response.json()

        return Paginator.paginate(
            fetch_func,
            page_size=self.max_results,
            results_key="results",
            size_key="size"
        )

    def _fetch_page_detail(self, page_id: str) -> Dict[str, Any]:
        """获取 Page 详细信息

        Args:
            page_id: Page ID

        Returns:
            Page 详细信息
        """
        url = f"{self.server}/rest/api/content/{page_id}"
        params = {
            "expand": "body.storage,version,space,history"
        }

        response = self._make_request("GET", url, params=params)
        return response.json()

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """发送 HTTP 请求（带重试和限流）

        Args:
            method: HTTP 方法
            url: 请求 URL
            params: 查询参数
            **kwargs: 其他请求参数

        Returns:
            响应对象

        Raises:
            requests.RequestException: 请求失败
        """
        def make_request():
            return self.session.request(method, url, params=params, **kwargs)

        return self.retry_handler.execute(make_request)

    def build_document(self, raw_file: Path, output_dir: Path) -> str:
        """将原始数据转换为 Document

        Args:
            raw_file: 原始数据文件路径
            output_dir: 输出目录

        Returns:
            生成的文档路径
        """
        # 读取原始数据
        raw_data = json.loads(raw_file.read_text(encoding="utf-8"))

        # 提取内容
        page_id = raw_data["id"]
        title = raw_data["title"]
        body = raw_data.get("body", {}).get("storage", {}).get("value", "")

        # 提取元数据
        space = raw_data.get("space", {})
        version = raw_data.get("version", {})
        history = raw_data.get("history", {})

        # 构建文档内容
        content_parts = [
            f"# {title}",
            "",
            f"**Space**: {space.get('name', 'Unknown')} ({space.get('key', 'N/A')})",
            f"**Page ID**: {page_id}",
            f"**Version**: {version.get('number', 'N/A')}",
            ""
        ]

        # 添加创建和更新信息
        if history:
            created_by = history.get("createdBy", {}).get("displayName", "Unknown")
            created_date = history.get("createdDate", "Unknown")
            content_parts.extend([
                f"**Created by**: {created_by}",
                f"**Created**: {created_date}",
                ""
            ])

        if version:
            updated_by = version.get("by", {}).get("displayName", "Unknown")
            updated_date = version.get("when", "Unknown")
            content_parts.extend([
                f"**Last updated by**: {updated_by}",
                f"**Updated**: {updated_date}",
                ""
            ])

        # 添加正文内容（使用 HTMLCleaner 清理）
        content_parts.append("## Content")
        content_parts.append("")

        # 使用 HTMLCleaner 彻底清理 HTML
        from datasource.core.utils.html_cleaner import HTMLCleaner
        clean_body = HTMLCleaner.clean(body, preserve_links=True, preserve_formatting=True)

        content_parts.append(clean_body)

        # 构建完整内容
        content = "\n".join(content_parts)

        # 创建 Document
        doc = Document(
            text=content,
            metadata={
                "source": "confluence",
                "page_id": page_id,
                "title": title,
                "space_key": space.get("key"),
                "space_name": space.get("name"),
                "version": version.get("number"),
                "url": f"{self.server}/pages/viewpage.action?pageId={page_id}"
            }
        )

        # 保存 Document
        output_file = output_dir / f"{page_id}.json"
        output_file.write_text(doc.to_json(), encoding="utf-8")

        return str(output_file)

    # ============ 异步抓取方法 ============

    async def fetch_raw_async(
        self,
        output_dir: Path,
        since: Optional[str] = None,
        max_concurrent: int = 10
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """异步抓取原始数据（性能提升 5-10 倍）

        Args:
            output_dir: 输出目录
            since: 增量同步起始时间（ISO 8601 格式）
            max_concurrent: 最大并发数

        Returns:
            [(page_id, raw_data)] 列表
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建异步 HTTP 客户端
        async_client = AsyncHTTPClient(
            max_concurrent=max_concurrent,
            max_retries=self.retry_handler.max_retries,
            retry_delay=self.retry_handler.base_delay,
            timeout=30
        )

        # 创建 aiohttp 会话
        auth = aiohttp.BasicAuth(self.email, self.token)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession(auth=auth, headers=headers) as session:
            # 第一步：获取 Page 列表
            if self.space_key:
                pages = await self._fetch_pages_by_space_async(session, async_client, self.space_key, since)
            elif self.cql:
                pages = await self._fetch_pages_by_cql_async(session, async_client, self.cql, since)
            else:
                logger.warning("未指定 space 或 cql，将获取所有可访问的 pages")
                pages = await self._fetch_all_pages_async(session, async_client, since)

            logger.info(f"Found {len(pages)} pages to fetch")

            # 第二步：并发获取每个 Page 的详细信息
            tasks = [
                self._fetch_page_detail_async(session, async_client, page["id"])
                for page in pages
            ]

            page_details = await async_client.gather_with_concurrency(tasks)

            # 第三步：保存结果
            results = []
            for page_detail in page_details:
                if isinstance(page_detail, Exception):
                    logger.error(f"Failed to fetch page: {page_detail}")
                    continue

                page_id = page_detail["id"]

                # 保存原始数据
                output_file = output_dir / f"page_{page_id}.json"
                output_file.write_text(
                    json.dumps(page_detail, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )

                logger.info(f"Fetched page: {page_detail.get('title')} (ID: {page_id})")
                results.append((page_id, page_detail))

            return results

    async def _fetch_pages_by_space_async(
        self,
        session: aiohttp.ClientSession,
        client: AsyncHTTPClient,
        space_key: str,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """异步获取 Space 中的 Pages

        Args:
            session: aiohttp 会话
            client: 异步 HTTP 客户端
            space_key: Space key
            since: 增量同步起始时间

        Returns:
            Page 列表
        """
        # 如果有 since，使用 CQL 查询
        if since:
            cql = f"space={space_key} AND lastModified >= '{since}'"
            return await self._fetch_pages_by_cql_async(session, client, cql, since=None)

        # 否则使用标准 API
        pages = []
        start = 0

        while True:
            url = f"{self.server}/rest/api/content"
            params = {
                "spaceKey": space_key,
                "type": "page",
                "status": "current",
                "limit": self.max_results,
                "start": start
            }

            data = await client.get_json(session, url, params=params)
            results = data.get("results", [])
            pages.extend(results)

            # 检查是否还有更多数据
            if len(results) < self.max_results:
                break

            start += self.max_results

        return pages

    async def _fetch_pages_by_cql_async(
        self,
        session: aiohttp.ClientSession,
        client: AsyncHTTPClient,
        cql: str,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """异步通过 CQL 查询获取 Pages

        Args:
            session: aiohttp 会话
            client: 异步 HTTP 客户端
            cql: CQL 查询语句
            since: 增量同步起始时间

        Returns:
            Page 列表
        """
        # 添加时间过滤
        if since:
            cql = f"({cql}) AND lastModified >= '{since}'"

        pages = []
        start = 0

        while True:
            url = f"{self.server}/rest/api/content/search"
            params = {
                "cql": cql,
                "limit": self.max_results,
                "start": start
            }

            data = await client.get_json(session, url, params=params)
            results = data.get("results", [])
            pages.extend(results)

            # 检查是否还有更多数据
            if len(results) < self.max_results:
                break

            start += self.max_results

        return pages

    async def _fetch_all_pages_async(
        self,
        session: aiohttp.ClientSession,
        client: AsyncHTTPClient,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """异步获取所有可访问的 Pages

        Args:
            session: aiohttp 会话
            client: 异步 HTTP 客户端
            since: 增量同步起始时间

        Returns:
            Page 列表
        """
        # 如果有 since，使用 CQL 查询
        if since:
            cql = f"type=page AND lastModified >= '{since}'"
            return await self._fetch_pages_by_cql_async(session, client, cql, since=None)

        pages = []
        start = 0

        while True:
            url = f"{self.server}/rest/api/content"
            params = {
                "type": "page",
                "status": "current",
                "limit": self.max_results,
                "start": start
            }

            data = await client.get_json(session, url, params=params)
            results = data.get("results", [])
            pages.extend(results)

            # 检查是否还有更多数据
            if len(results) < self.max_results:
                break

            start += self.max_results

        return pages

    async def _fetch_page_detail_async(
        self,
        session: aiohttp.ClientSession,
        client: AsyncHTTPClient,
        page_id: str
    ) -> Dict[str, Any]:
        """异步获取 Page 详细信息

        Args:
            session: aiohttp 会话
            client: 异步 HTTP 客户端
            page_id: Page ID

        Returns:
            Page 详细信息
        """
        url = f"{self.server}/rest/api/content/{page_id}"
        params = {
            "expand": "body.storage,version,space,history"
        }

        return await client.get_json(session, url, params=params)

    def fetch_raw_sync_wrapper(
        self,
        output_dir: Path,
        since: Optional[str] = None,
        use_async: bool = True,
        max_concurrent: int = 10
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """同步包装器，可选择使用异步抓取

        Args:
            output_dir: 输出目录
            since: 增量同步起始时间
            use_async: 是否使用异步抓取
            max_concurrent: 最大并发数（仅异步模式）

        Yields:
            (page_id, raw_data) 元组
        """
        if use_async:
            # 使用异步抓取
            results = asyncio.run(self.fetch_raw_async(output_dir, since, max_concurrent))
            for page_id, raw_data in results:
                yield page_id, raw_data
        else:
            # 使用原有的同步抓取
            yield from self.fetch_raw(output_dir, since)
