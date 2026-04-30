"""Jira Issue 实时加载器

复用 datasource 的 JiraDataSource，提供实时拉取 issue 的能力。
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# 添加 datasource 到 Python 路径
datasource_path = Path(__file__).parent.parent.parent.parent / "datasource"
if str(datasource_path) not in sys.path:
    sys.path.insert(0, str(datasource_path))

import aiohttp
from datasource.core.utils.async_http import AsyncHTTPClient

from ..exceptions import IssueLoadError
from ..utils.error_handling import handle_errors, retry_on_error

logger = logging.getLogger(__name__)


class IssueLoader:
    """Jira Issue 实时加载器

    职责：
    - 实时从 Jira API 拉取目标 issue 的最新数据
    - 支持单个和批量加载
    - 使用异步方式提升性能
    """

    def __init__(
        self,
        server: str,
        email: str,
        token: str,
        max_concurrent: int = 10
    ):
        """初始化 Issue Loader

        Args:
            server: Jira Server URL
            email: 用户邮箱
            token: API Token
            max_concurrent: 最大并发请求数
        """
        self.server = server.rstrip('/')
        self.email = email
        self.token = token
        self.max_concurrent = max_concurrent

        # 创建异步 HTTP 客户端
        self.http_client = AsyncHTTPClient(
            max_concurrent=max_concurrent,
            max_retries=3,
            retry_delay=1.0,
            timeout=30
        )

        logger.info(f"IssueLoader initialized: server={self.server}")

    async def load_issue_realtime(self, issue_key: str) -> Dict[str, Any]:
        """实时拉取单个 issue（包含 comments）

        Args:
            issue_key: Issue key (如 PROJ-123)

        Returns:
            完整的 issue 数据

        Raises:
            Exception: 拉取失败
        """
        auth = aiohttp.BasicAuth(self.email, self.token)

        async with aiohttp.ClientSession(auth=auth) as session:
            url = f"{self.server}/rest/api/2/issue/{issue_key}"
            params = {
                "expand": "renderedFields,names,schema,transitions,operations,changelog,comments"
            }

            try:
                data = await self.http_client.get_json(session, url, params=params)
                logger.info(f"Loaded issue: {issue_key}")
                return data
            except Exception as e:
                logger.error(f"Failed to load issue {issue_key}: {e}")
                raise

    async def load_issues_batch(self, issue_keys: List[str]) -> List[Dict[str, Any]]:
        """批量实时拉取（异步并发）

        Args:
            issue_keys: Issue key 列表

        Returns:
            Issue 数据列表（保持顺序，失败的为 None）
        """
        auth = aiohttp.BasicAuth(self.email, self.token)

        async with aiohttp.ClientSession(auth=auth) as session:
            # 创建任务
            tasks = [
                self._fetch_issue_async(session, issue_key)
                for issue_key in issue_keys
            ]

            # 并发执行
            results = await self.http_client.gather_with_concurrency(
                tasks, return_exceptions=True
            )

            # 处理结果
            issues = []
            for issue_key, result in zip(issue_keys, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to load issue {issue_key}: {result}")
                    issues.append(None)
                else:
                    logger.info(f"Loaded issue: {issue_key}")
                    issues.append(result)

            success_count = sum(1 for issue in issues if issue is not None)
            logger.info(f"Batch load completed: {success_count}/{len(issue_keys)} succeeded")

            return issues

    async def _fetch_issue_async(
        self,
        session: aiohttp.ClientSession,
        issue_key: str
    ) -> Dict[str, Any]:
        """异步获取单个 issue

        Args:
            session: aiohttp 会话
            issue_key: Issue key

        Returns:
            Issue 数据
        """
        url = f"{self.server}/rest/api/2/issue/{issue_key}"
        params = {
            "expand": "renderedFields,names,schema,transitions,operations,changelog,comments"
        }

        return await self.http_client.get_json(session, url, params=params)

    async def search_issues_by_jql(
        self,
        jql: str,
        max_results: int = 100
    ) -> List[str]:
        """通过 JQL 查询获取 issue keys

        Args:
            jql: JQL 查询语句
            max_results: 最大结果数

        Returns:
            Issue key 列表
        """
        auth = aiohttp.BasicAuth(self.email, self.token)
        issue_keys = []

        async with aiohttp.ClientSession(auth=auth) as session:
            start_at = 0
            page_size = 50

            while len(issue_keys) < max_results:
                url = f"{self.server}/rest/api/2/search"
                params = {
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": min(page_size, max_results - len(issue_keys)),
                    "fields": "key"
                }

                try:
                    data = await self.http_client.get_json(session, url, params=params)
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
                    logger.error(f"Failed to search issues at offset {start_at}: {e}")
                    break

        logger.info(f"Found {len(issue_keys)} issues for JQL: {jql}")
        return issue_keys
