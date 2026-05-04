"""混合检索器

结合向量检索和 BM25 检索，提供统一的检索接口。
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore
from llama_index.core import VectorStoreIndex
from llama_index.retrievers.bm25 import BM25Retriever

from .vector import VectorIndexer
from .bm25 import BM25Indexer

logger = logging.getLogger(__name__)


class HybridRetriever:
    """混合检索器

    结合向量检索和 BM25 检索，支持：
    1. 混合检索（Vector + BM25）
    2. 单一检索（仅 Vector 或仅 BM25）
    3. 可配置的权重
    4. 结果去重和排序
    """

    def __init__(
        self,
        vector_index: Optional[VectorStoreIndex] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        top_k: int = 5
    ):
        """初始化混合检索器

        Args:
            vector_index: 向量索引
            bm25_retriever: BM25 检索器
            vector_weight: 向量检索权重（默认 0.6）
            bm25_weight: BM25 检索权重（默认 0.4）
            top_k: 返回结果数量
        """
        self.vector_index = vector_index
        self.bm25_retriever = bm25_retriever
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.top_k = top_k

        # 验证权重
        if abs(vector_weight + bm25_weight - 1.0) > 0.01:
            logger.warning(
                f"权重之和不为 1.0: vector={vector_weight}, bm25={bm25_weight}"
            )

        logger.info(
            f"HybridRetriever initialized: vector_weight={vector_weight}, "
            f"bm25_weight={bm25_weight}, top_k={top_k}"
        )

    @classmethod
    def from_persist_dirs(
        cls,
        vector_dir: Path,
        bm25_dir: Path,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        top_k: int = 5
    ) -> "HybridRetriever":
        """从持久化目录加载检索器

        Args:
            vector_dir: 向量索引目录
            bm25_dir: BM25 索引目录
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
            top_k: 返回结果数量

        Returns:
            HybridRetriever 实例
        """
        # 加载向量索引
        vector_indexer = VectorIndexer()
        vector_index = vector_indexer.load_index(vector_dir)

        # 加载 BM25 索引
        bm25_indexer = BM25Indexer()
        bm25_retriever = bm25_indexer.load_index(bm25_dir)

        return cls(
            vector_index=vector_index,
            bm25_retriever=bm25_retriever,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            top_k=top_k
        )

    def retrieve(
        self,
        query: str,
        mode: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None,
        filter_doc_ids: Optional[List[str]] = None
    ) -> List[NodeWithScore]:
        """执行检索

        Args:
            query: 查询字符串
            mode: 检索模式 - "hybrid", "vector", "bm25"
            filters: 元数据过滤条件（字段级别）
            filter_doc_ids: 文档 ID 白名单，只在这些文档中检索

        Returns:
            检索结果列表（NodeWithScore）
        """
        if mode == "vector":
            return self._retrieve_vector(query, filters, filter_doc_ids)
        elif mode == "bm25":
            return self._retrieve_bm25(query, filters, filter_doc_ids)
        elif mode == "hybrid":
            return self._retrieve_hybrid(query, filters, filter_doc_ids)
        else:
            raise ValueError(f"不支持的检索模式: {mode}")

    def _retrieve_vector(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        filter_doc_ids: Optional[List[str]] = None
    ) -> List[NodeWithScore]:
        """向量检索

        Args:
            query: 查询字符串
            filters: 元数据过滤条件
            filter_doc_ids: 文档 ID 白名单

        Returns:
            检索结果列表
        """
        if not self.vector_index:
            logger.warning("向量索引未加载")
            return []

        # 创建检索器（不使用 filters 参数，因为需要 MetadataFilters 对象）
        retriever = self.vector_index.as_retriever(
            similarity_top_k=self.top_k
        )

        results = retriever.retrieve(query)

        # 应用文档 ID 过滤
        if filter_doc_ids:
            results = self._apply_doc_id_filter(results, filter_doc_ids)

        # 手动应用字段过滤器
        if filters:
            results = self._apply_filters(results, filters)

        logger.info(f"Vector retrieval returned {len(results)} results")
        return results

    def _retrieve_bm25(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        filter_doc_ids: Optional[List[str]] = None
    ) -> List[NodeWithScore]:
        """BM25 检索

        Args:
            query: 查询字符串
            filters: 元数据过滤条件
            filter_doc_ids: 文档 ID 白名单

        Returns:
            检索结果列表
        """
        if not self.bm25_retriever:
            logger.warning("BM25 索引未加载")
            return []

        # BM25Retriever 使用 QueryBundle
        query_bundle = QueryBundle(query_str=query)
        results = self.bm25_retriever.retrieve(query_bundle)

        # 应用文档 ID 过滤
        if filter_doc_ids:
            results = self._apply_doc_id_filter(results, filter_doc_ids)

        # 应用字段过滤器（如果有）
        if filters:
            results = self._apply_filters(results, filters)

        logger.info(f"BM25 retrieval returned {len(results)} results")
        return results[:self.top_k]

    def _retrieve_hybrid(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        filter_doc_ids: Optional[List[str]] = None
    ) -> List[NodeWithScore]:
        """混合检索

        Args:
            query: 查询字符串
            filters: 元数据过滤条件
            filter_doc_ids: 文档 ID 白名单

        Returns:
            检索结果列表
        """
        # 获取两种检索结果
        vector_results = self._retrieve_vector(query, filters, filter_doc_ids)
        bm25_results = self._retrieve_bm25(query, filters, filter_doc_ids)

        # 合并和重新评分
        combined = self._combine_results(vector_results, bm25_results)

        logger.info(f"Hybrid retrieval returned {len(combined)} results")
        return combined[:self.top_k]

    def _combine_results(
        self,
        vector_results: List[NodeWithScore],
        bm25_results: List[NodeWithScore]
    ) -> List[NodeWithScore]:
        """合并两种检索结果

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25 检索结果

        Returns:
            合并后的结果列表
        """
        # 使用字典去重（按 node_id）
        node_scores: Dict[str, float] = {}

        # 添加向量检索结果
        for node_with_score in vector_results:
            node_id = node_with_score.node.node_id
            score = node_with_score.score or 0.0
            node_scores[node_id] = score * self.vector_weight

        # 添加 BM25 检索结果
        for node_with_score in bm25_results:
            node_id = node_with_score.node.node_id
            score = node_with_score.score or 0.0
            if node_id in node_scores:
                # 已存在，累加分数
                node_scores[node_id] += score * self.bm25_weight
            else:
                node_scores[node_id] = score * self.bm25_weight

        # 重建 NodeWithScore 列表
        all_nodes = {n.node.node_id: n for n in vector_results + bm25_results}
        combined = []
        for node_id, score in node_scores.items():
            node_with_score = all_nodes[node_id]
            # 更新分数
            node_with_score.score = score
            combined.append(node_with_score)

        # 按分数降序排序
        combined.sort(key=lambda x: x.score or 0.0, reverse=True)

        return combined

    def _apply_filters(
        self,
        results: List[NodeWithScore],
        filters: Dict[str, Any]
    ) -> List[NodeWithScore]:
        """应用元数据过滤

        Args:
            results: 检索结果
            filters: 过滤条件

        Returns:
            过滤后的结果
        """
        filtered = []
        for node_with_score in results:
            metadata = node_with_score.node.metadata
            match = True
            for key, value in filters.items():
                if metadata.get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(node_with_score)

        return filtered

    def _apply_doc_id_filter(
        self,
        results: List[NodeWithScore],
        filter_doc_ids: List[str]
    ) -> List[NodeWithScore]:
        """应用文档 ID 过滤

        Args:
            results: 检索结果
            filter_doc_ids: 允许的文档 ID 列表

        Returns:
            过滤后的结果
        """
        if not filter_doc_ids:
            return results

        # 转换为集合以提高查找效率
        allowed_ids = set(filter_doc_ids)

        filtered = []
        for node_with_score in results:
            # 检查 node_id 或 metadata 中的 doc_id
            node_id = node_with_score.node.node_id
            doc_id = node_with_score.node.metadata.get("doc_id", node_id)

            if doc_id in allowed_ids or node_id in allowed_ids:
                filtered.append(node_with_score)

        logger.info(f"Doc ID filter: {len(results)} -> {len(filtered)} results")
        return filtered
