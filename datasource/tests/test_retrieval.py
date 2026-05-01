"""测试混合检索功能"""

import pytest
from pathlib import Path
from llama_index.core import Document

from datasource.core.indexing.vector import VectorIndexer
from datasource.core.indexing.bm25 import BM25Indexer
from datasource.core.indexing.hybrid import HybridRetriever


@pytest.fixture
def sample_documents():
    """创建示例文档"""
    return [
        Document(
            text="Python is a high-level programming language used for web development, data science, and automation.",
            metadata={"source": "doc1", "type": "tutorial"}
        ),
        Document(
            text="LlamaIndex is a powerful framework for building LLM applications with retrieval augmented generation.",
            metadata={"source": "doc2", "type": "documentation"}
        ),
        Document(
            text="Vector databases store embeddings for semantic search and similarity matching in AI applications.",
            metadata={"source": "doc3", "type": "article"}
        ),
        Document(
            text="BM25 is a ranking function used in information retrieval for keyword-based search.",
            metadata={"source": "doc4", "type": "article"}
        ),
    ]


@pytest.fixture
def indexed_dirs(sample_documents, tmp_path):
    """创建已索引的目录"""
    vector_dir = tmp_path / "vector"
    bm25_dir = tmp_path / "bm25"

    # 构建向量索引
    vector_indexer = VectorIndexer(chunk_size=256)
    vector_indexer.build_index(sample_documents, vector_dir)

    # 构建 BM25 索引
    bm25_indexer = BM25Indexer(chunk_size=256)
    bm25_indexer.build_index(sample_documents, bm25_dir)

    return vector_dir, bm25_dir


class TestHybridRetriever:
    """测试混合检索器"""

    def test_from_persist_dirs(self, indexed_dirs):
        """测试从持久化目录加载"""
        vector_dir, bm25_dir = indexed_dirs

        # 创建混合检索器
        retriever = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir,
            top_k=3
        )

        # 验证创建成功
        assert retriever is not None
        assert retriever.vector_index is not None
        assert retriever.bm25_retriever is not None

    def test_hybrid_retrieve(self, indexed_dirs):
        """测试混合检索"""
        vector_dir, bm25_dir = indexed_dirs

        retriever = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir,
            top_k=3
        )

        # 执行检索
        results = retriever.retrieve("What is Python?", mode="hybrid")

        # 验证结果
        assert len(results) > 0
        assert len(results) <= 3
        assert all(hasattr(r, "node") for r in results)
        assert all(hasattr(r, "score") for r in results)

    def test_vector_only_retrieve(self, indexed_dirs):
        """测试仅向量检索"""
        vector_dir, bm25_dir = indexed_dirs

        retriever = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir,
            top_k=3
        )

        # 执行检索
        results = retriever.retrieve("What is Python?", mode="vector")

        # 验证结果
        assert len(results) > 0
        assert len(results) <= 3

    def test_bm25_only_retrieve(self, indexed_dirs):
        """测试仅 BM25 检索"""
        vector_dir, bm25_dir = indexed_dirs

        retriever = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir,
            top_k=3
        )

        # 执行检索
        results = retriever.retrieve("Python programming", mode="bm25")

        # 验证结果
        assert len(results) > 0
        assert len(results) <= 3

    def test_invalid_mode(self, indexed_dirs):
        """测试无效的检索模式"""
        vector_dir, bm25_dir = indexed_dirs

        retriever = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir
        )

        # 应该抛出异常
        with pytest.raises(ValueError, match="不支持的检索模式"):
            retriever.retrieve("test", mode="invalid")

    def test_retrieve_with_filters(self, indexed_dirs):
        """测试带过滤条件的检索"""
        vector_dir, bm25_dir = indexed_dirs

        retriever = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir,
            top_k=5
        )

        # 执行带过滤的检索
        filters = {"type": "article"}
        results = retriever.retrieve("search", mode="hybrid", filters=filters)

        # 验证结果都符合过滤条件
        for result in results:
            assert result.node.metadata.get("type") == "article"

    def test_custom_weights(self, indexed_dirs):
        """测试自定义权重"""
        vector_dir, bm25_dir = indexed_dirs

        # 创建不同权重的检索器
        retriever1 = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir,
            vector_weight=0.8,
            bm25_weight=0.2,
            top_k=3
        )

        retriever2 = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir,
            vector_weight=0.2,
            bm25_weight=0.8,
            top_k=3
        )

        # 验证权重设置
        assert retriever1.vector_weight == 0.8
        assert retriever1.bm25_weight == 0.2
        assert retriever2.vector_weight == 0.2
        assert retriever2.bm25_weight == 0.8

    def test_top_k_limit(self, indexed_dirs):
        """测试 top_k 限制"""
        vector_dir, bm25_dir = indexed_dirs

        retriever = HybridRetriever.from_persist_dirs(
            vector_dir=vector_dir,
            bm25_dir=bm25_dir,
            top_k=2
        )

        # 执行检索
        results = retriever.retrieve("Python LlamaIndex", mode="hybrid")

        # 验证结果数量不超过 top_k
        assert len(results) <= 2

    def test_retrieve_without_vector_index(self, indexed_dirs):
        """测试没有向量索引时的检索"""
        _, bm25_dir = indexed_dirs

        # 加载 BM25 索引
        bm25_indexer = BM25Indexer()
        bm25_retriever = bm25_indexer.load_index(bm25_dir)

        # 创建只有 BM25 的检索器
        retriever = HybridRetriever(
            vector_index=None,
            bm25_retriever=bm25_retriever,
            top_k=3
        )

        # 向量检索应该返回空
        results = retriever.retrieve("test", mode="vector")
        assert len(results) == 0

        # BM25 检索应该正常工作
        results = retriever.retrieve("Python", mode="bm25")
        assert len(results) > 0

    def test_retrieve_without_bm25_index(self, indexed_dirs):
        """测试没有 BM25 索引时的检索"""
        vector_dir, _ = indexed_dirs

        # 加载向量索引
        vector_indexer = VectorIndexer()
        vector_index = vector_indexer.load_index(vector_dir)

        # 创建只有向量的检索器
        retriever = HybridRetriever(
            vector_index=vector_index,
            bm25_retriever=None,
            top_k=3
        )

        # BM25 检索应该返回空
        results = retriever.retrieve("test", mode="bm25")
        assert len(results) == 0

        # 向量检索应该正常工作
        results = retriever.retrieve("Python", mode="vector")
        assert len(results) > 0
