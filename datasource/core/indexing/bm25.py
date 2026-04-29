"""BM25 索引构建器

使用 LlamaIndex BM25Retriever 构建 BM25 索引。
"""

import logging
import pickle
from pathlib import Path
from typing import List, Optional

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.retrievers.bm25 import BM25Retriever

logger = logging.getLogger(__name__)


class BM25Indexer:
    """BM25 索引构建器

    负责：
    1. 从 Documents 构建 BM25 索引
    2. 使用 IngestionPipeline 自动切分 Nodes
    3. 持久化索引到本地文件系统
    4. 加载已有索引
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        k1: float = 1.5,
        b: float = 0.75
    ):
        """初始化 BM25 索引构建器

        Args:
            chunk_size: 文本切分大小
            chunk_overlap: 切分重叠大小
            k1: BM25 参数 k1（控制词频饱和度）
            b: BM25 参数 b（控制文档长度归一化）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k1 = k1
        self.b = b

        # 创建文本切分器
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        logger.info(
            f"BM25Indexer initialized: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, k1={k1}, b={b}"
        )

    def build_index(
        self,
        documents: List[Document],
        persist_dir: Path
    ) -> BM25Retriever:
        """构建 BM25 索引

        Args:
            documents: 文档列表
            persist_dir: 索引持久化目录

        Returns:
            BM25Retriever: 构建的检索器
        """
        if not documents:
            raise ValueError("文档列表不能为空")

        logger.info(f"Building BM25 index from {len(documents)} documents")

        # 使用 IngestionPipeline 处理文档
        pipeline = IngestionPipeline(
            transformations=[self.splitter]
        )

        nodes = pipeline.run(documents=documents)
        logger.info(f"Created {len(nodes)} nodes from documents")

        # 构建 BM25 检索器
        retriever = BM25Retriever.from_defaults(
            nodes=nodes,
            similarity_top_k=10
        )

        # 持久化（保存 nodes 而不是 retriever）
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._persist_nodes(nodes, persist_dir)
        logger.info(f"BM25 index persisted to: {persist_dir}")

        return retriever

    def load_index(self, persist_dir: Path) -> Optional[BM25Retriever]:
        """加载已有索引

        Args:
            persist_dir: 索引目录

        Returns:
            BM25Retriever 或 None（如果不存在）
        """
        if not persist_dir.exists():
            logger.warning(f"Index directory not found: {persist_dir}")
            return None

        try:
            nodes = self._load_nodes(persist_dir)
            retriever = BM25Retriever.from_defaults(
                nodes=nodes,
                similarity_top_k=10
            )
            logger.info(f"BM25 index loaded from: {persist_dir}")
            return retriever
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
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

        # 尝试加载节点数
        node_count = 0
        try:
            nodes = self._load_nodes(persist_dir)
            node_count = len(nodes) if nodes else 0
        except Exception:
            pass

        return {
            "exists": True,
            "node_count": node_count,
            "size_mb": round(size_mb, 2)
        }

    def _persist_nodes(self, nodes: list, persist_dir: Path):
        """持久化节点列表

        Args:
            nodes: 节点列表
            persist_dir: 持久化目录
        """
        # 保存 nodes
        nodes_file = persist_dir / "nodes.pkl"
        with open(nodes_file, "wb") as f:
            pickle.dump(nodes, f)

        # 保存配置
        config_file = persist_dir / "config.pkl"
        config = {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "k1": self.k1,
            "b": self.b
        }
        with open(config_file, "wb") as f:
            pickle.dump(config, f)

    def _load_nodes(self, persist_dir: Path) -> list:
        """加载节点列表

        Args:
            persist_dir: 持久化目录

        Returns:
            节点列表
        """
        # 加载 nodes
        nodes_file = persist_dir / "nodes.pkl"
        with open(nodes_file, "rb") as f:
            nodes = pickle.load(f)

        return nodes
