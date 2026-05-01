"""异步 HTTP 客户端工具

提供基于 aiohttp 的异步 HTTP 请求功能，支持：
- 并发控制（Semaphore）
- 自动重试和指数退避
- 429 限流处理
- 超时控制
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum

import aiohttp

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"  # 固定延迟
    EXPONENTIAL = "exponential"  # 指数退避


class AsyncHTTPClient:
    """异步 HTTP 客户端

    使用 aiohttp 实现异步 HTTP 请求，支持并发控制和重试机制。
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        timeout: int = 30
    ):
        """初始化异步 HTTP 客户端

        Args:
            max_concurrent: 最大并发请求数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            retry_strategy: 重试策略
            timeout: 请求超时时间（秒）
        """
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_strategy = retry_strategy
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """发送异步 HTTP 请求（带重试和限流）

        Args:
            session: aiohttp 会话
            method: HTTP 方法
            url: 请求 URL
            **kwargs: 其他请求参数

        Returns:
            响应对象

        Raises:
            aiohttp.ClientError: 请求失败
        """
        async with self.semaphore:
            for attempt in range(self.max_retries):
                try:
                    async with session.request(
                        method,
                        url,
                        timeout=self.timeout,
                        **kwargs
                    ) as response:
                        # 处理限流
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                            logger.warning(f"Rate limited, waiting {retry_after}s...")
                            await asyncio.sleep(retry_after)
                            continue

                        response.raise_for_status()
                        return response

                except aiohttp.ClientError as e:
                    if attempt < self.max_retries - 1:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                        )
                        logger.info(f"Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                        raise

            raise aiohttp.ClientError(f"Failed after {self.max_retries} retries")

    async def get_json(
        self,
        session: aiohttp.ClientSession,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送 GET 请求并返回 JSON

        Args:
            session: aiohttp 会话
            url: 请求 URL
            **kwargs: 其他请求参数

        Returns:
            JSON 响应数据
        """
        async with self.semaphore:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(
                        url,
                        timeout=self.timeout,
                        **kwargs
                    ) as response:
                        # 处理限流
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                            logger.warning(f"Rate limited, waiting {retry_after}s...")
                            await asyncio.sleep(retry_after)
                            continue

                        response.raise_for_status()
                        return await response.json()

                except aiohttp.ClientError as e:
                    if attempt < self.max_retries - 1:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                        )
                        logger.info(f"Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                        raise

            raise aiohttp.ClientError(f"Failed after {self.max_retries} retries")

    async def gather_with_concurrency(
        self,
        tasks: list,
        return_exceptions: bool = True
    ) -> list:
        """并发执行任务（带并发控制）

        Args:
            tasks: 协程任务列表
            return_exceptions: 是否返回异常而不是抛出

        Returns:
            任务结果列表
        """
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)

    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟

        Args:
            attempt: 当前重试次数（从 0 开始）

        Returns:
            延迟时间（秒）
        """
        if self.retry_strategy == RetryStrategy.FIXED:
            return self.retry_delay
        else:  # EXPONENTIAL
            return self.retry_delay * (2 ** attempt)
