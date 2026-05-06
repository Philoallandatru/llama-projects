"""Confluence 数据源实现

支持从 Confluence Server 抓取 Pages 和附件。
"""

import logging
import json
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any, Optional, List
from datetime import datetime

from llama_index.core import Document
from atlassian import Confluence

from .base import BaseDataSource

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

        # 使用 atlassian-python-api 创建 Confluence 客户端
        self.confluence_client = Confluence(
            url=self.server,
            username=self.email,
            password=self.token,
            cloud=True  # Atlassian Cloud
        )

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
            logger.info("=" * 60)
            logger.info("Starting Confluence data fetch")
            logger.info(f"Server: {self.server}")
            logger.info(f"Space: {self.space_key or 'All spaces'}")
            logger.info(f"CQL: {self.cql or 'None'}")
            logger.info(f"Since: {since or 'Full sync'}")
            logger.info("=" * 60)

            if self.space_key:
                logger.info(f"Fetching pages from space: {self.space_key}")
                pages = self._fetch_pages_by_space(self.space_key, since)
            elif self.cql:
                logger.info(f"Fetching pages with CQL: {self.cql}")
                pages = self._fetch_pages_by_cql(self.cql, since)
            else:
                logger.warning("未指定 space 或 cql，将获取所有可访问的 pages")
                pages = self._fetch_all_pages(since)

            # 转换为列表以获取总数
            pages_list = list(pages)
            total_pages = len(pages_list)
            logger.info(f"Found {total_pages} pages to fetch")

            # 保存每个 Page
            for idx, page in enumerate(pages_list, 1):
                page_id = page["id"]

                logger.info(f"[{idx}/{total_pages}] Fetching page detail: {page.get('title', 'Unknown')} (ID: {page_id})")

                # 获取完整的 Page 内容
                page_detail = self._fetch_page_detail(page_id)

                # 保存原始数据
                output_file = output_dir / f"page_{page_id}.json"
                output_file.write_text(json.dumps(page_detail, ensure_ascii=False, indent=2), encoding="utf-8")

                logger.info(f"[{idx}/{total_pages}] ✓ Saved: {page_detail.get('title')} ({len(page_detail.get('body', {}).get('storage', {}).get('value', ''))} chars)")

                yield page_id, page_detail

            logger.info("=" * 60)
            logger.info(f"Confluence fetch completed: {total_pages} pages")
            logger.info("=" * 60)

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

        # 使用 atlassian-python-api 获取 space 中的所有页面
        pages = []
        start = 0
        limit = self.max_results

        while True:
            result = self.confluence_client.get_all_pages_from_space(
                space=space_key,
                start=start,
                limit=limit,
                expand='body.storage,version,space,history,ancestors'
            )

            if not result:
                break

            pages.extend(result)

            if len(result) < limit:
                break

            start += limit

        return pages

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

        # 使用 atlassian-python-api 的 cql 方法
        pages = []
        start = 0
        limit = self.max_results

        while True:
            result = self.confluence_client.cql(
                cql=cql,
                start=start,
                limit=limit,
                expand='body.storage,version,space,history,ancestors'
            )

            if not result or 'results' not in result:
                break

            pages.extend(result['results'])

            if len(result['results']) < limit:
                break

            start += limit

        return pages

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

        # 使用 atlassian-python-api 获取所有页面
        pages = []
        start = 0
        limit = self.max_results

        while True:
            result = self.confluence_client.get_all_pages_from_space(
                space='',  # 空字符串表示所有 space
                start=start,
                limit=limit,
                status='current',
                expand='body.storage,version,space,history,ancestors'
            )

            if not result:
                break

            pages.extend(result)

            if len(result) < limit:
                break

            start += limit

        return pages

    def _fetch_page_detail(self, page_id: str) -> Dict[str, Any]:
        """获取 Page 详细信息

        Args:
            page_id: Page ID

        Returns:
            Page 详细信息
        """
        # 使用 atlassian-python-api 获取页面详情
        page = self.confluence_client.get_page_by_id(
            page_id=page_id,
            expand='body.storage,version,space,history,ancestors'
        )
        return page


    def build_document(
        self,
        item_id: str,
        raw_data: Dict[str, Any],
        assets_dir: Path
    ) -> Document:
        """将 Confluence 页面转换为 LlamaIndex Document

        Args:
            item_id: 页面 ID
            raw_data: 原始页面数据
            assets_dir: 资源目录（未使用）

        Returns:
            LlamaIndex Document 对象
        """

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
                "url": f"{self.server}/pages/viewpage.action?pageId={page_id}",
                "created_date": history.get("createdDate") if history else None,
                "updated_date": version.get("when") if version else None
            }
        )

        return doc
