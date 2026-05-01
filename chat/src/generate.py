import logging
import os
import sys

# 添加 datasource 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../datasource'))

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def generate_index():
    """
    从多数据源生成索引
    """
    from src.index import STORAGE_DIR, get_source_manager
    from src.settings import init_settings
    from src.datasource_config import get_enabled_datasources
    from llama_index.core.indices import VectorStoreIndex
    from llama_index.core.readers import SimpleDirectoryReader

    load_dotenv()
    init_settings()

    # 获取 SourceManager
    manager = get_source_manager()

    if manager is None:
        logger.warning("SourceManager not available, falling back to SimpleDirectoryReader")
        # 回退到原始方法
        reader = SimpleDirectoryReader(
            os.environ.get("DATA_DIR", "ui/data"),
            recursive=True,
        )
        documents = reader.load_data()
    else:
        # 使用 datasource 系统
        logger.info("Using datasource system for multi-source indexing")

        # 获取启用的数据源
        enabled_sources = get_enabled_datasources()
        logger.info(f"Found {len(enabled_sources)} enabled data sources")

        # 添加数据源（如果尚未添加）
        existing_sources = {s.name for s in manager.list_sources()}

        for ds_config in enabled_sources:
            name = ds_config["name"]

            if name not in existing_sources:
                logger.info(f"Adding data source: {name}")
                try:
                    manager.add_source(
                        name=name,
                        source_type=ds_config["type"],
                        config=ds_config["config"]
                    )
                except Exception as e:
                    logger.error(f"Failed to add source {name}: {e}")
                    continue
            else:
                logger.info(f"Data source already exists: {name}")

        # 同步所有数据源并加载文档
        all_documents = []
        for source in manager.list_sources():
            logger.info(f"Syncing source: {source.name}")
            try:
                manager.sync_source(source.name)

                # 加载文档
                docs = manager.load_documents(source.name)
                logger.info(f"Loaded {len(docs)} documents from {source.name}")
                all_documents.extend(docs)
            except Exception as e:
                logger.error(f"Failed to sync source {source.name}: {e}")
                continue

        documents = all_documents

    # 创建索引
    logger.info(f"Creating index from {len(documents)} documents")
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True,
    )

    # 持久化
    index.storage_context.persist(STORAGE_DIR)
    logger.info(f"Finished creating new index. Stored in {STORAGE_DIR}")
