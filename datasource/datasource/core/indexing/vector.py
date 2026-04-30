"""向量索引构建器

使用 LlamaIndex VectorStoreIndex 构建向量索引。
"""

import logging
from pathlib import Path
from typing import List, Optional

from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Document,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline

logger = logging.getLogger(__name__)


class VectorIndexer:
    """向量索引构建器

    负责：
    1. 从 Documents 构建向量索引
    2. 使用 IngestionPipeline 自动切分 Nodes
    3. 持久化索引到本地文件系统
    4. 加载已有索引
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        embed_model: Optional[str] = None
    ):
        """初始化向量索引构建器

        Args:
            chunk_size: 文本切分大小
            chunk_overlap: 切分重叠大小
            embed_model: 嵌入模型名称（None 使用默认）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embed_model = embed_model

        # 创建文本切分器
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        logger.info(
            f"VectorIndexer initialized: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}"
        )

    def build_index(
        self,
        documents: List[Document],
        persist_dir: Path
    ) -> VectorStoreIndex:
        """构建向量索引

        Args:
            documents: 文档列表
            persist_dir: 索引持久化目录

        Returns:
            VectorStoreIndex: 构建的索引
        """
        if not documents:
            raise ValueError("文档列表不能为空")

        logger.info(f"Building vector index from {len(documents)} documents")

        # 使用 IngestionPipeline 处理文档
        pipeline = IngestionPipeline(
            transformations=[self.splitter]
        )

        nodes = pipeline.run(documents=documents)
        logger.info(f"Created {len(nodes)} nodes from documents")

        # 构建索引
        index = VectorStoreIndex(nodes)

        # 持久化
        persist_dir.mkdir(parents=True, exist_ok=True)
        index.storage_context.persist(persist_dir=str(persist_dir))
        logger.info(f"Vector index persisted to: {persist_dir}")

        return index

    def load_index(self, persist_dir: Path) -> Optional[VectorStoreIndex]:
        """加载已有索引

        Args:
            persist_dir: 索引目录

        Returns:
            VectorStoreIndex 或 None（如果不存在）
        """
        if not persist_dir.exists():
            logger.warning(f"Index directory not found: {persist_dir}")
            return None

        try:
            storage_context = StorageContext.from_defaults(
                persist_dir=str(persist_dir)
            )
            index = load_index_from_storage(storage_context)
            logger.info(f"Vector index loaded from: {persist_dir}")
            return index
        except Exception as e:
            logger.error(f"Failed to load vector index: {e}")
            return None

    def get_stats(self, persist_dir: Path) -> dict:
        """获取索引统计信息

        Args:
            persist_dir: 索引目录

        Returns:
            统计信息字典
        """
        if not persist_dir.exists():
            return {
                "exists": False,
                "node_count": 0,
                "size_mb": 0.0
            }

        # 计算目录大小
        total_size = sum(
            f.stat().st_size for f in persist_dir.rglob("*") if f.is_file()
        )
        size_mb = total_size / (1024 * 1024)

        # 尝试加载索引获取节点数
        node_count = 0
        try:
            index = self.load_index(persist_dir)
            if index:
                node_count = len(index.docstore.docs)
        except Exception:
            pass

        return {
            "exists": True,
            "node_count": node_count,
            "size_mb": round(size_mb, 2)
        }
