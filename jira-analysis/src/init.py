"""初始化设置和日志配置"""

import logging
import sys
from pathlib import Path

from .settings import settings


def init_settings() -> None:
    """初始化设置和日志"""
    setup_logging()
    validate_settings()


def setup_logging() -> None:
    """配置日志"""
    log_level = logging.INFO

    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # 文件处理器（可选）
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "jira-analysis.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 减少第三方库的日志噪音
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


def validate_settings() -> None:
    """验证必需的设置"""
    errors = []

    # 检查 Jira 配置
    if not settings.jira_server:
        errors.append("JIRA_SERVER not set")
    if not settings.jira_token:
        errors.append("JIRA_TOKEN not set")

    # 检查 LLM 配置
    if not settings.llm_base_url:
        errors.append("LLM_BASE_URL not set")
    if not settings.llm_model:
        errors.append("LLM_MODEL not set")

    # 检查索引路径
    index_base = Path(settings.index_base_path)
    if not index_base.exists():
        logging.warning(f"Index base path does not exist: {index_base}")

    if errors:
        logging.error("Configuration errors found:")
        for error in errors:
            logging.error(f"  - {error}")
        raise ValueError("Invalid configuration. Please check your .env file.")

    logging.info("Settings validated successfully")
