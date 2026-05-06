import logging
import os
import sys

# 添加 datasource 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../datasource'))

from llama_index.core.indices import load_index_from_storage
from llama_index.core.storage import StorageContext

logger = logging.getLogger("uvicorn")

STORAGE_DIR = "src/storage"
DATA_DIR = "src/datasource_data"  # datasource 数据目录


def get_source_manager():
    """获取 SourceManager 实例"""
    try:
        from pathlib import Path
        from datasource.core.manager import SourceManager

        data_dir = Path(DATA_DIR)
        return SourceManager(data_dir)
    except ImportError as e:
        logger.error(f"Failed to import datasource: {e}")
        logger.error("Make sure datasource is installed: cd ../datasource && pip install -e .")
        return None


def get_index():
    # check if storage already exists
    if not os.path.exists(STORAGE_DIR):
        return None
    # load the existing index
    logger.info(f"Loading index from {STORAGE_DIR}...")
    storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
    index = load_index_from_storage(storage_context)
    logger.info(f"Finished loading index from {STORAGE_DIR}")
    return index
