import logging
import os
import sys
from pathlib import Path

# 添加 datasource 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../datasource'))

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def generate_index():
    """
    从多数据源生成索引

    使用 datasource 系统同步数据并构建索引
    """
    from settings import init_settings
    from datasource_config import get_enabled_datasources

    load_dotenv()
    init_settings()

    # 使用 datasource 系统
    try:
        from datasource.core.manager import SourceManager
        from datasource.core.models import SourceConfig, SourceType

        # 创建 SourceManager
        data_dir = Path(__file__).parent / "datasource_data"
        manager = SourceManager(data_dir=data_dir)
        logger.info(f"Using datasource system with data_dir: {data_dir}")

        # 获取启用的数据源配置
        enabled_sources = get_enabled_datasources()
        logger.info(f"Found {len(enabled_sources)} enabled data sources")

        if not enabled_sources:
            logger.error("No enabled data sources found! Please check config.yaml")
            return

        # 获取已存在的数据源
        existing_sources = {s.name for s in manager.list_sources()}

        # 添加新数据源
        for ds_config in enabled_sources:
            name = ds_config["name"]
            ds_type = ds_config["type"]
            config = ds_config["config"]

            if name in existing_sources:
                logger.info(f"Data source already exists: {name}")
                continue

            logger.info(f"Adding data source: {name} (type: {ds_type})")

            try:
                # 构建 SourceConfig
                if ds_type == "local":
                    source_config = SourceConfig(
                        name=name,
                        type=SourceType.LOCAL,
                        path=config.get("directory"),
                        description=ds_config.get("description", "")
                    )
                elif ds_type == "jira":
                    source_config = SourceConfig(
                        name=name,
                        type=SourceType.JIRA,
                        server=config.get("server_url"),
                        jql=config.get("jql"),
                        description=ds_config.get("description", ""),
                        options={
                            "email": config.get("email"),
                            "token": config.get("token")
                        }
                    )
                elif ds_type == "confluence":
                    source_config = SourceConfig(
                        name=name,
                        type=SourceType.CONFLUENCE,
                        server=config.get("base_url"),
                        space=config.get("space_key"),
                        cql=config.get("cql"),
                        description=ds_config.get("description", ""),
                        options={
                            "email": config.get("email"),
                            "token": config.get("token")
                        }
                    )
                else:
                    logger.error(f"Unknown source type: {ds_type}")
                    continue

                manager.add_source(source_config)
                logger.info(f"Successfully added source: {name}")

            except Exception as e:
                logger.error(f"Failed to add source {name}: {e}")
                continue

        # 同步所有数据源（这会自动构建索引）
        success_count = 0
        for source_info in manager.list_sources():
            logger.info(f"Syncing source: {source_info.name}")
            try:
                # 同步数据源（自动构建 vector 和 BM25 索引）
                sync_result = manager.sync_source(source_info.name)
                logger.info(
                    f"Sync completed: {sync_result.document_count} docs, "
                    f"{sync_result.error_count} errors"
                )
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to sync source {source_info.name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        if success_count == 0:
            logger.error("No sources synced successfully!")
            return

        logger.info(f"Successfully synced {success_count} data sources")
        logger.info("Indexes are ready for querying")

    except ImportError as e:
        logger.error(f"Datasource system not available: {e}")
        logger.error("Please install datasource: cd ../datasource && uv sync")
        raise


if __name__ == "__main__":
    generate_index()
