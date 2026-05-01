"""HTTP 请求重试工具

提供统一的重试和限流处理逻辑。
"""

import time
import logging
from typing import Callable, TypeVar, Optional
from functools import wraps

import requests

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryHandler:
    """HTTP 请求重试处理器

    支持：
    - 自动重试失败的请求
    - 处理 429 限流响应
    - 指数退避或固定延迟策略
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 5.0,
        backoff_strategy: str = "fixed",  # "fixed" or "exponential"
        handle_rate_limit: bool = True
    ):
        """初始化重试处理器

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            backoff_strategy: 退避策略，"fixed" 或 "exponential"
            handle_rate_limit: 是否自动处理 429 限流响应
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_strategy = backoff_strategy
        self.handle_rate_limit = handle_rate_limit

    def execute(self, func: Callable[[], requests.Response]) -> requests.Response:
        """执行带重试的请求

        Args:
            func: 返回 requests.Response 的函数

        Returns:
            requests.Response 对象

        Raises:
            requests.RequestException: 请求失败
        """
        for attempt in range(self.max_retries):
            try:
                response = func()

                # 处理 429 限流
                if self.handle_rate_limit and response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.base_delay))
                    logger.warning(f"Rate limited (429), waiting {retry_after}s before retry...")
                    time.sleep(retry_after)
                    continue

                # 检查其他错误
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    # 计算延迟时间
                    if self.backoff_strategy == "exponential":
                        delay = self.base_delay * (2 ** attempt)
                    else:
                        delay = self.base_delay

                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                    )
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise

        # 如果所有重试都因为 429 而失败
        raise requests.RequestException(f"Failed after {self.max_retries} retries")

    @staticmethod
    def request_with_retry(
        session: requests.Session,
        method: str,
        url: str,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        exponential_backoff: bool = False,
        **kwargs
    ) -> requests.Response:
        """带重试的 HTTP 请求（静态方法）

        Args:
            session: requests.Session 对象
            method: HTTP 方法（GET, POST, etc.）
            url: 请求 URL
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            exponential_backoff: 是否使用指数退避
            **kwargs: 传递给 session.request 的其他参数

        Returns:
            requests.Response 对象

        Raises:
            requests.RequestException: 请求失败

        Example:
            >>> session = requests.Session()
            >>> response = RetryHandler.request_with_retry(
            ...     session, "GET", "https://api.example.com/data",
            ...     max_retries=3, retry_delay=2.0
            ... )
        """
        handler = RetryHandler(
            max_retries=max_retries,
            base_delay=retry_delay,
            backoff_strategy="exponential" if exponential_backoff else "fixed"
        )
        return handler.execute(lambda: session.request(method, url, **kwargs))

    @staticmethod
    def retry_on_exception(
        max_retries: int = 3,
        retry_delay: float = 5.0,
        exponential_backoff: bool = False,
        exceptions: tuple = (Exception,)
    ):
        """装饰器：自动重试抛出异常的函数

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            exponential_backoff: 是否使用指数退避
            exceptions: 需要重试的异常类型元组

        Returns:
            装饰器函数

        Example:
            >>> @RetryHandler.retry_on_exception(max_retries=3, retry_delay=2.0)
            ... def fetch_data():
            ...     response = requests.get("https://api.example.com/data")
            ...     return response.json()
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        if attempt < max_retries - 1:
                            # 计算延迟时间
                            if exponential_backoff:
                                delay = retry_delay * (2 ** attempt)
                            else:
                                delay = retry_delay

                            logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}"
                            )
                            logger.info(f"Retrying in {delay}s...")
                            time.sleep(delay)
                        else:
                            logger.error(
                                f"{func.__name__} failed after {max_retries} attempts: {e}"
                            )
                            raise

                # 不应该到达这里
                raise RuntimeError(f"Unexpected state in retry logic")

            return wrapper
        return decorator


class RateLimiter:
    """简单的速率限制器

    用于控制请求频率，避免触发 API 限流。
    """

    def __init__(self, requests_per_second: float = 1.0):
        """初始化速率限制器

        Args:
            requests_per_second: 每秒允许的请求数
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time: Optional[float] = None

    def wait_if_needed(self):
        """如果需要，等待以满足速率限制"""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)

        self.last_request_time = time.time()

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """装饰器：自动应用速率限制

        Example:
            >>> limiter = RateLimiter(requests_per_second=2.0)
            >>> @limiter
            ... def fetch_data():
            ...     return requests.get("https://api.example.com/data")
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            self.wait_if_needed()
            return func(*args, **kwargs)

        return wrapper
