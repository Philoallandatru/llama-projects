"""测试索引构建功能"""

import pytest
from pathlib import Path
from llama_index.core import Document

from datasource.core.indexing.vector import VectorIndexer
from datasource.core.indexing.bm25 import BM25Indexer


@pytest.fixture
def sample_documents():
    """创建示例文档"""
    return [
        Document(
            text="Python is a high-level programming language.",
            metadata={"source": "doc1", "type": "tutorial"}
        ),
        Document(
            text="LlamaIndex is a framework for building LLM applications.",
            metadata={"source": "doc2", "type": "documentation"}
        ),
        Document(
            text="Vector databases store embeddings for semantic search.",
            metadata={"source": "doc3", "type": "article"}
        ),
    ]


class TestVectorIndexer:
    """测试向量索引构建器"""

    def test_build_index(self, sample_documents, tmp_path):
        """测试构建向量索引"""
        indexer = VectorIndexer(chunk_size=256, chunk_overlap=20)
        persist_dir = tmp_path / "vector"

        # 构建索引
        index = indexer.build_index(sample_documents, persist_dir)

        # 验证索引创建成功
        assert index is not None
        assert persist_dir.exists()
        assert len(list(persist_dir.iterdir())) > 0

    def test_load_index(self, sample_documents, tmp_path):
        """测试加载向量索引"""
        indexer = VectorIndexer()
        persist_dir = tmp_path / "vector"

        # 先构建索引
        indexer.build_index(sample_documents, persist_dir)

        # 加载索引
        loaded_index = indexer.load_index(persist_dir)

        # 验证加载成功
        assert loaded_index is not None

    def test_load_nonexistent_index(self, tmp_path):
        """测试加载不存在的索引"""
        indexer = VectorIndexer()
        persist_dir = tmp_path / "nonexistent"

        # 加载不存在的索引
        loaded_index = indexer.load_index(persist_dir)

        # 应该返回 None
        assert loaded_index is None

    def test_get_stats(self, sample_documents, tmp_path):
        """测试获取索引统计信息"""
        indexer = VectorIndexer()
        persist_dir = tmp_path / "vector"

        # 构建索引前
        stats_before = indexer.get_stats(persist_dir)
        assert stats_before["exists"] is False
        assert stats_before["node_count"] == 0

        # 构建索引
        indexer.build_index(sample_documents, persist_dir)

        # 构建索引后
        stats_after = indexer.get_stats(persist_dir)
        assert stats_after["exists"] is True
        assert stats_after["size_mb"] > 0

    def test_build_index_empty_documents(self, tmp_path):
        """测试空文档列表"""
        indexer = VectorIndexer()
        persist_dir = tmp_path / "vector"

        # 应该抛出异常
        with pytest.raises(ValueError, match="文档列表不能为空"):
            indexer.build_index([], persist_dir)


class TestBM25Indexer:
    """测试 BM25 索引构建器"""

    def test_build_index(self, sample_documents, tmp_path):
        """测试构建 BM25 索引"""
        indexer = BM25Indexer(chunk_size=256, chunk_overlap=20)
        persist_dir = tmp_path / "bm25"

        # 构建索引
        retriever = indexer.build_index(sample_documents, persist_dir)

        # 验证索引创建成功
        assert retriever is not None
        assert persist_dir.exists()
        assert (persist_dir / "nodes.pkl").exists()
        assert (persist_dir / "config.pkl").exists()

    def test_load_index(self, sample_documents, tmp_path):
        """测试加载 BM25 索引"""
        indexer = BM25Indexer()
        persist_dir = tmp_path / "bm25"

        # 先构建索引
        indexer.build_index(sample_documents, persist_dir)

        # 加载索引
        loaded_retriever = indexer.load_index(persist_dir)

        # 验证加载成功
        assert loaded_retriever is not None

    def test_load_nonexistent_index(self, tmp_path):
        """测试加载不存在的索引"""
        indexer = BM25Indexer()
        persist_dir = tmp_path / "nonexistent"

        # 加载不存在的索引
        loaded_retriever = indexer.load_index(persist_dir)

        # 应该返回 None
        assert loaded_retriever is None

    def test_get_stats(self, sample_documents, tmp_path):
        """测试获取索引统计信息"""
        indexer = BM25Indexer()
        persist_dir = tmp_path / "bm25"

        # 构建索引前
        stats_before = indexer.get_stats(persist_dir)
        assert stats_before["exists"] is False
        assert stats_before["node_count"] == 0

        # 构建索引
        indexer.build_index(sample_documents, persist_dir)

        # 构建索引后
        stats_after = indexer.get_stats(persist_dir)
        assert stats_after["exists"] is True
        assert stats_after["node_count"] > 0
        assert stats_after["size_mb"] >= 0  # 可能很小，接近0

    def test_build_index_empty_documents(self, tmp_path):
        """测试空文档列表"""
        indexer = BM25Indexer()
        persist_dir = tmp_path / "bm25"

        # 应该抛出异常
        with pytest.raises(ValueError, match="文档列表不能为空"):
            indexer.build_index([], persist_dir)
