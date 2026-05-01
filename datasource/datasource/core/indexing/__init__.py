"""索引构建模块

提供向量索引和 BM25 索引的构建功能。
"""

from .vector import VectorIndexer
from .bm25 import BM25Indexer

# 延迟导入避免循环依赖
def get_hybrid_retriever():
    from .hybrid import HybridRetriever
    return HybridRetriever

__all__ = ["VectorIndexer", "BM25Indexer", "get_hybrid_retriever"]
