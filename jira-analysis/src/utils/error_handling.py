"""错误处理装饰器和工具"""

import functools
import logging
from typing import Callable, TypeVar, Any

from .exceptions import (
    JiraAnalysisError,
    IssueLoadError,
    EvidenceRetrievalError,
    LLMGenerationError,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


def handle_errors(
    error_message: str = "Operation failed",
    raise_on_error: bool = True,
    default_return: Any = None
) -> Callable:
    """错误处理装饰器

    Args:
        error_message: 错误消息前缀
        raise_on_error: 是否重新抛出异常
        default_return: 发生错误时的默认返回值

    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except JiraAnalysisError as e:
                logger.error(f"{error_message}: {e}")
                if raise_on_error:
                    raise
                return default_return
            except Exception as e:
                logger.error(f"{error_message}: Unexpected error: {e}", exc_info=True)
                if raise_on_error:
                    raise JiraAnalysisError(f"{error_message}: {e}") from e
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except JiraAnalysisError as e:
                logger.error(f"{error_message}: {e}")
                if raise_on_error:
                    raise
                return default_return
            except Exception as e:
                logger.error(f"{error_message}: Unexpected error: {e}", exc_info=True)
                if raise_on_error:
                    raise JiraAnalysisError(f"{error_message}: {e}") from e
                return default_return

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍增因子
        exceptions: 需要重试的异常类型

    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            import asyncio

            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries failed")

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            import time

            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries failed")

            raise last_exception

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
