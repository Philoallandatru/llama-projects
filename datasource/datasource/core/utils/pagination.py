"""通用分页工具

提供统一的分页逻辑，避免代码重复。
"""

from typing import Callable, Dict, Any, List, TypeVar, Optional
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Paginator:
    """通用分页器

    用于处理各种 REST API 的分页逻辑。
    """

    @staticmethod
    def paginate(
        fetch_func: Callable[[int, int], Dict[str, Any]],
        page_size: int = 50,
        max_results: Optional[int] = None,
        start_key: str = "start",
        results_key: str = "results",
        size_key: str = "size"
    ) -> List[T]:
        """通用分页逻辑

        Args:
            fetch_func: 抓取函数，接受 (start, limit) 返回响应字典
            page_size: 每页大小
            max_results: 最大结果数（None 表示无限制）
            start_key: 响应中起始位置的键名（用于某些 API）
            results_key: 响应中结果列表的键名
            size_key: 响应中当前页大小的键名

        Returns:
            所有结果列表

        Example:
            >>> def fetch(start, limit):
            ...     response = requests.get(url, params={"start": start, "limit": limit})
            ...     return response.json()
            >>> results = Paginator.paginate(fetch, page_size=50)
        """
        all_results = []
        start = 0

        while True:
            # 计算本次抓取数量
            limit = page_size
            if max_results:
                remaining = max_results - len(all_results)
                if remaining <= 0:
                    break
                limit = min(limit, remaining)

            # 抓取一页
            try:
                response = fetch_func(start, limit)
            except Exception as e:
                logger.error(f"Pagination fetch failed at start={start}: {e}")
                break

            # 提取结果
            batch = response.get(results_key, [])

            if not batch:
                break

            all_results.extend(batch)
            logger.debug(f"Fetched {len(batch)} items (total: {len(all_results)})")

            # 检查是否还有更多数据
            current_size = response.get(size_key, len(batch))
            if current_size < limit:
                # 当前页不满，说明没有更多数据了
                break

            # 更新起始位置
            start += limit

        logger.info(f"Pagination completed: {len(all_results)} total items")
        return all_results

    @staticmethod
    def paginate_with_next_link(
        fetch_func: Callable[[Optional[str]], Dict[str, Any]],
        results_key: str = "results",
        next_key: str = "next"
    ) -> List[T]:
        """使用 next 链接的分页逻辑

        适用于返回 next URL 的 API（如 GitHub、GitLab）。

        Args:
            fetch_func: 抓取函数，接受 next_url 返回响应字典
            results_key: 响应中结果列表的键名
            next_key: 响应中下一页链接的键名

        Returns:
            所有结果列表

        Example:
            >>> def fetch(next_url):
            ...     url = next_url or base_url
            ...     response = requests.get(url)
            ...     return response.json()
            >>> results = Paginator.paginate_with_next_link(fetch)
        """
        all_results = []
        next_url = None

        while True:
            try:
                response = fetch_func(next_url)
            except Exception as e:
                logger.error(f"Pagination fetch failed: {e}")
                break

            # 提取结果
            batch = response.get(results_key, [])

            if not batch:
                break

            all_results.extend(batch)
            logger.debug(f"Fetched {len(batch)} items (total: {len(all_results)})")

            # 获取下一页链接
            next_url = response.get(next_key)
            if not next_url:
                break

        logger.info(f"Pagination completed: {len(all_results)} total items")
        return all_results

    @staticmethod
    def paginate_cursor_based(
        fetch_func: Callable[[Optional[str], int], Dict[str, Any]],
        page_size: int = 50,
        max_results: Optional[int] = None,
        results_key: str = "results",
        cursor_key: str = "cursor",
        has_more_key: str = "has_more"
    ) -> List[T]:
        """基于游标的分页逻辑

        适用于使用游标分页的 API（如 Notion、Stripe）。

        Args:
            fetch_func: 抓取函数，接受 (cursor, limit) 返回响应字典
            page_size: 每页大小
            max_results: 最大结果数（None 表示无限制）
            results_key: 响应中结果列表的键名
            cursor_key: 响应中游标的键名
            has_more_key: 响应中是否有更多数据的键名

        Returns:
            所有结果列表

        Example:
            >>> def fetch(cursor, limit):
            ...     params = {"limit": limit}
            ...     if cursor:
            ...         params["cursor"] = cursor
            ...     response = requests.get(url, params=params)
            ...     return response.json()
            >>> results = Paginator.paginate_cursor_based(fetch, page_size=50)
        """
        all_results = []
        cursor = None

        while True:
            # 计算本次抓取数量
            limit = page_size
            if max_results:
                remaining = max_results - len(all_results)
                if remaining <= 0:
                    break
                limit = min(limit, remaining)

            # 抓取一页
            try:
                response = fetch_func(cursor, limit)
            except Exception as e:
                logger.error(f"Pagination fetch failed at cursor={cursor}: {e}")
                break

            # 提取结果
            batch = response.get(results_key, [])

            if not batch:
                break

            # 如果有 max_results 限制，只添加需要的数量
            if max_results:
                remaining = max_results - len(all_results)
                batch = batch[:remaining]

            all_results.extend(batch)
            logger.debug(f"Fetched {len(batch)} items (total: {len(all_results)})")

            # 检查是否达到 max_results
            if max_results and len(all_results) >= max_results:
                break

            # 检查是否还有更多数据
            has_more = response.get(has_more_key, False)
            if not has_more:
                break

            # 更新游标
            cursor = response.get(cursor_key)
            if not cursor:
                break

        logger.info(f"Pagination completed: {len(all_results)} total items")
        return all_results
