"""数据源管理器

负责数据源的创建、删除、列表、同步等操作。
"""

import logging
from pathlib import Path
from typing import List, Optional

from .models import SourceConfig, SourceInfo, SourceType, SyncResult
from .paths import Paths
from .sources.base import BaseDataSource
from .sources.local import LocalDataSource

logger = logging.getLogger(__name__)


class SourceManager:
    """数据源管理器

    负责：
    - 数据源的创建和删除
    - 数据源配置的持久化
    - 数据源实例的创建
    - 数据源列表和详情查询
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """初始化管理器

        Args:
            data_dir: 数据目录，默认为 ./data
        """
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths = Paths(self.data_dir)
        logger.info(f"SourceManager initialized with data_dir: {self.data_dir}")

    def add_source(self, config: SourceConfig) -> SourceInfo:
        """添加数据源

        Args:
            config: 数据源配置

        Returns:
            SourceInfo: 数据源信息

        Raises:
            ValueError: 如果数据源已存在
        """
        # 检查是否已存在
        if self.paths.exists(config.name):
            raise ValueError(f"数据源 '{config.name}' 已存在")

        # 创建目录结构
        self.paths.ensure_dirs(config.name)
        logger.info(f"Created directories for source: {config.name}")

        # 保存配置
        config_path = self.paths.source_config(config.name)
        config_path.write_text(config.to_yaml(), encoding="utf-8")
        logger.info(f"Saved config to: {config_path}")

        # 返回数据源信息
        return self.get_source_info(config.name)

    def delete_source(self, name: str, force: bool = False) -> None:
        """删除数据源

        Args:
            name: 数据源名称
            force: 是否强制删除（不提示确认）

        Raises:
            ValueError: 如果数据源不存在
        """
        if not self.paths.exists(name):
            raise ValueError(f"数据源 '{name}' 不存在")

        # 删除整个目录
        import shutil
        source_dir = self.paths.source(name)
        shutil.rmtree(source_dir)
        logger.info(f"Deleted source: {name}")

    def list_sources(self) -> List[SourceInfo]:
        """列出所有数据源

        Returns:
            List[SourceInfo]: 数据源信息列表
        """
        source_names = self.paths.list_sources()
        return [self.get_source_info(name) for name in source_names]

    def get_source_info(self, name: str) -> SourceInfo:
        """获取数据源详情

        Args:
            name: 数据源名称

        Returns:
            SourceInfo: 数据源信息

        Raises:
            ValueError: 如果数据源不存在
        """
        if not self.paths.exists(name):
            raise ValueError(f"数据源 '{name}' 不存在")

        # 读取配置
        config_path = self.paths.source_config(name)
        if not config_path.exists():
            raise ValueError(f"数据源 '{name}' 配置文件不存在")

        config = SourceConfig.from_yaml(config_path.read_text(encoding="utf-8"))

        # 读取 manifest（如果存在）
        manifest_path = self.paths.manifest(name)
        manifest = None
        if manifest_path.exists():
            import json
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        # 计算统计信息
        raw_dir = self.paths.raw(name)
        doc_dir = self.paths.documents(name)
        raw_count = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0
        doc_count = len(list(doc_dir.glob("*.json"))) if doc_dir.exists() else 0

        return SourceInfo(
            name=config.name,
            type=config.type,
            config=config,
            raw_count=raw_count,
            document_count=doc_count,
            total_size=self.paths.get_size_mb(name),
            last_sync=manifest.get("last_sync") if manifest else None,
            status=manifest.get("status", "未同步") if manifest else "未同步"
        )

    def sync_source(self, name: str) -> SyncResult:
        """同步数据源

        执行流程：
        1. fetch_raw() - 抓取原始数据
        2. build_document() - 构建文档
        3. 保存 manifest

        Args:
            name: 数据源名称

        Returns:
            SyncResult: 同步结果

        Raises:
            ValueError: 如果数据源不存在
        """
        if not self.paths.exists(name):
            raise ValueError(f"数据源 '{name}' 不存在")

        # 读取配置
        config_path = self.paths.source_config(name)
        config = SourceConfig.from_yaml(config_path.read_text(encoding="utf-8"))

        # 创建数据源实例
        source = self._create_source(config)

        # 执行同步
        logger.info(f"Starting sync for source: {name}")

        from datetime import datetime
        import json

        raw_count = 0
        doc_count = 0
        errors = []

        try:
            # 1. 抓取原始数据
            raw_dir = self.paths.raw(name)
            doc_dir = self.paths.documents(name)
            assets_dir = self.paths.assets(name)

            for item_id, raw_data in source.fetch_raw(raw_dir):
                raw_count += 1

                try:
                    # 2. 构建文档
                    doc = source.build_document(item_id, raw_data, assets_dir)

                    # 3. 保存文档
                    doc_file = doc_dir / f"{source._sanitize_filename(item_id)}.json"
                    doc_file.write_text(doc.to_json(), encoding="utf-8")
                    doc_count += 1

                except Exception as e:
                    error_msg = f"Failed to process {item_id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # 保存 manifest
            manifest = {
                "last_sync": datetime.now().isoformat(),
                "status": "已同步" if not errors else "部分失败",
                "raw_count": raw_count,
                "document_count": doc_count,
                "error_count": len(errors),
                "errors": errors[:10]  # 只保留前10个错误
            }

            manifest_path = self.paths.manifest(name)
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

            result = SyncResult(
                success=len(errors) == 0,
                raw_count=raw_count,
                document_count=doc_count,
                error_count=len(errors),
                errors=errors
            )

            logger.info(f"Sync completed for source: {name}, raw: {raw_count}, docs: {doc_count}, errors: {len(errors)}")
            return result

        except Exception as e:
            logger.error(f"Sync failed for source: {name}, error: {e}")
            raise

    def _create_source(self, config: SourceConfig) -> BaseDataSource:
        """创建数据源实例

        Args:
            config: 数据源配置

        Returns:
            BaseDataSource: 数据源实例

        Raises:
            ValueError: 如果数据源类型不支持
        """
        if config.type == SourceType.LOCAL:
            if not config.path:
                raise ValueError("本地文件数据源必须指定 path")
            return LocalDataSource(config)
        elif config.type == SourceType.JIRA:
            # TODO: 实现 JiraDataSource
            raise NotImplementedError("Jira 数据源尚未实现")
        elif config.type == SourceType.CONFLUENCE:
            # TODO: 实现 ConfluenceDataSource
            raise NotImplementedError("Confluence 数据源尚未实现")
        else:
            raise ValueError(f"不支持的数据源类型: {config.type}")
