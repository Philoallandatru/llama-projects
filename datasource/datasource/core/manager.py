"""数据源管理器

负责数据源的创建、删除、列表、同步等操作。
"""

import logging
from pathlib import Path
from typing import List, Optional

from llama_index.core import Document

from .models import SourceConfig, SourceInfo, SourceType, SyncResult
from .paths import Paths
from .sources.base import BaseDataSource
from .sources.local import LocalDataSource
from .sources.jira import JiraDataSource
from .sources.confluence import ConfluenceDataSource
from .indexing.vector import VectorIndexer
from .indexing.bm25 import BM25Indexer
from .indexing.hybrid import HybridRetriever
from .metadata.metadata_index import MetadataIndex
import json
from datetime import datetime

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

        # 初始化元数据索引
        metadata_db_path = self.data_dir / "metadata.db"
        self.metadata_index = MetadataIndex(metadata_db_path)

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

    def sync_source(self, name: str, full: bool = False) -> SyncResult:
        """同步数据源

        执行流程：
        1. fetch_raw() - 抓取原始数据（支持增量同步）
        2. build_document() - 构建文档
        3. 保存 manifest

        Args:
            name: 数据源名称
            full: 是否强制全量同步（默认 False，使用增量同步）

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
        from datetime import datetime
        import json

        # 读取上次同步时间（用于增量同步）
        manifest_path = self.paths.manifest(name)
        last_sync_time = None
        if not full and manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                last_sync_time = manifest.get("last_sync")
                if last_sync_time:
                    logger.info(f"Incremental sync from: {last_sync_time}")
            except Exception as e:
                logger.warning(f"Failed to read last sync time: {e}, performing full sync")

        sync_mode = "full" if full or not last_sync_time else "incremental"
        logger.info(f"Starting {sync_mode} sync for source: {name}")

        raw_count = 0
        doc_count = 0
        errors = []

        try:
            # 1. 抓取原始数据
            raw_dir = self.paths.raw(name)
            doc_dir = self.paths.documents(name)
            assets_dir = self.paths.assets(name)

            # 传递 since 参数进行增量同步
            since = None if full else last_sync_time
            for item_id, raw_data in source.fetch_raw(raw_dir, since=since):
                raw_count += 1

                try:
                    # 2. 构建文档
                    doc = source.build_document(item_id, raw_data, assets_dir)

                    # 3. 提取并存储元数据（如果是 Jira/Confluence）
                    if config.type == SourceType.JIRA:
                        self.metadata_index.add_jira_metadata(item_id, doc.metadata)
                    elif config.type == SourceType.CONFLUENCE:
                        self.metadata_index.add_confluence_metadata(item_id, doc.metadata)

                    # 4. 保存文档
                    doc_file = doc_dir / f"{source._sanitize_filename(item_id)}.json"
                    doc_file.write_text(doc.to_json(), encoding="utf-8")
                    doc_count += 1

                except Exception as e:
                    error_msg = f"Failed to process {item_id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # 4. 构建索引
            logger.info(f"Building indexes for source: {name}")
            index_errors = self._build_indexes(name, doc_dir)
            errors.extend(index_errors)

            # 保存 manifest
            current_time = datetime.now().isoformat()
            manifest = {
                "last_sync": current_time,
                "last_full_sync": current_time if full else manifest.get("last_full_sync", current_time) if manifest_path.exists() and not full else current_time,
                "sync_mode": sync_mode,
                "status": "已同步" if not errors else "部分失败",
                "raw_count": raw_count,
                "document_count": doc_count,
                "error_count": len(errors),
                "errors": errors[:10]  # 只保留前10个错误
            }

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

    def query(
        self,
        name: str,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
        filter_doc_ids: Optional[List[str]] = None
    ) -> List[dict]:
        """查询数据源

        Args:
            name: 数据源名称
            query: 查询字符串
            mode: 检索模式 - "hybrid", "vector", "bm25"
            top_k: 返回结果数量
            filter_doc_ids: 可选的文档 ID 列表，只在这些文档中检索

        Returns:
            查询结果列表

        Raises:
            ValueError: 如果数据源不存在或索引未构建
        """
        if not self.paths.exists(name):
            raise ValueError(f"数据源 '{name}' 不存在")

        # 验证查询字符串
        if not query or not query.strip():
            logger.warning("Empty query string, returning empty results")
            return []

        # 检查索引是否存在
        vector_dir = self.paths.indexes(name) / "vector"
        bm25_dir = self.paths.indexes(name) / "bm25"

        # 检查向量索引
        vector_exists = vector_dir.exists() and (vector_dir / "docstore.json").exists()
        # 检查 BM25 索引
        bm25_exists = bm25_dir.exists() and (bm25_dir / "nodes.pkl").exists()

        if not vector_exists and not bm25_exists:
            raise ValueError(f"数据源 '{name}' 的索引尚未构建，请先运行 sync 命令")

        # 创建混合检索器
        retriever = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir,
            top_k=top_k
        )

        # 执行检索（传递 filter_doc_ids）
        results = retriever.retrieve(query, mode=mode, filter_doc_ids=filter_doc_ids)

        # 转换为字典格式
        output = []
        for i, node_with_score in enumerate(results, 1):
            node = node_with_score.node
            output.append({
                "rank": i,
                "score": round(node_with_score.score or 0.0, 4),
                "text": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                "metadata": node.metadata,
                "node_id": node.node_id
            })

        logger.info(f"Query returned {len(output)} results for source: {name}")
        return output

    def _build_indexes(self, name: str, doc_dir: Path) -> List[str]:
        """构建索引

        Args:
            name: 数据源名称
            doc_dir: 文档目录

        Returns:
            错误列表
        """
        errors = []

        try:
            # 加载所有文档
            documents = []
            for doc_file in doc_dir.glob("*.json"):
                try:
                    doc_json = doc_file.read_text(encoding="utf-8")
                    doc = Document.from_json(doc_json)
                    documents.append(doc)
                except Exception as e:
                    error_msg = f"Failed to load document {doc_file.name}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            if not documents:
                logger.warning("No documents to index")
                return errors

            logger.info(f"Loaded {len(documents)} documents for indexing")

            # 构建向量索引
            try:
                vector_indexer = VectorIndexer()
                vector_dir = self.paths.indexes(name) / "vector"
                vector_indexer.build_index(documents, vector_dir)
                logger.info("Vector index built successfully")
            except Exception as e:
                error_msg = f"Failed to build vector index: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

            # 构建 BM25 索引
            try:
                bm25_indexer = BM25Indexer()
                bm25_dir = self.paths.indexes(name) / "bm25"
                bm25_indexer.build_index(documents, bm25_dir)
                logger.info("BM25 index built successfully")
            except Exception as e:
                error_msg = f"Failed to build BM25 index: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        except Exception as e:
            error_msg = f"Failed to build indexes: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return errors

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
            if not config.server:
                raise ValueError("Jira 数据源必须指定 server")
            return JiraDataSource(config)
        elif config.type == SourceType.CONFLUENCE:
            if not config.server:
                raise ValueError("Confluence 数据源必须指定 server")
            return ConfluenceDataSource(config)
        else:
            raise ValueError(f"不支持的数据源类型: {config.type}")
