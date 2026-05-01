"""日志配置工具"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> None:
    """配置日志系统

    Args:
        level: 日志级别
        log_file: 日志文件路径（可选）
        format_string: 日志格式字符串（可选）
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    formatter = logging.Formatter(
        format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    handlers = [console_handler]

    # 文件处理器（如果指定）
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        handlers.append(file_handler)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 清除现有处理器
    root_logger.handlers.clear()

    # 添加新处理器
    for handler in handlers:
        root_logger.addHandler(handler)

    # 减少第三方库的日志噪音
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        Logger 实例
    """
    return logging.getLogger(name)
