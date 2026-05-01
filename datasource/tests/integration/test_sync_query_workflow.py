"""集成测试 - 完整的同步和查询工作流"""

import pytest
from pathlib import Path

from datasource.core.manager import SourceManager
from datasource.core.models import SourceConfig, SourceType


@pytest.fixture
def test_data_dir(tmp_path):
    """创建测试数据目录"""
    data_dir = tmp_path / "test_docs"
    data_dir.mkdir()

    # 创建测试文件
    (data_dir / "doc1.txt").write_text("Python is a programming language.", encoding="utf-8")
    (data_dir / "doc2.txt").write_text("LlamaIndex is a framework for LLM applications.", encoding="utf-8")
    (data_dir / "doc3.txt").write_text("Vector databases store embeddings for search.", encoding="utf-8")

    return data_dir


@pytest.fixture
def manager(tmp_path):
    """创建 SourceManager 实例"""
    return SourceManager(tmp_path / "data")


class TestSyncAndQueryWorkflow:
    """测试完整的同步和查询工作流"""

    def test_full_workflow(self, manager, test_data_dir):
        """测试完整工作流：添加 -> 同步 -> 查询"""
        source_name = "test_source"

        # 1. 添加数据源
        config = SourceConfig(
            name=source_name,
            type=SourceType.LOCAL,
            path=str(test_data_dir)
        )
        info = manager.add_source(config)

        assert info.name == source_name
        assert info.type == SourceType.LOCAL

        # 2. 同步数据源
        result = manager.sync_source(source_name)

        assert result.success is True
        assert result.raw_count == 3
        assert result.document_count == 3
        assert result.error_count == 0

        # 3. 查询数据源
        query_results = manager.query(source_name, "Python programming")

        assert len(query_results) > 0
        assert all("score" in r for r in query_results)
        assert all("text" in r for r in query_results)
        assert all("metadata" in r for r in query_results)

    def test_query_different_modes(self, manager, test_data_dir):
        """测试不同的查询模式"""
        source_name = "test_source"

        # 添加并同步
        config = SourceConfig(
            name=source_name,
            type=SourceType.LOCAL,
            path=str(test_data_dir)
        )
        manager.add_source(config)
        manager.sync_source(source_name)

        # 测试混合检索
        hybrid_results = manager.query(source_name, "Python", mode="hybrid", top_k=2)
        assert len(hybrid_results) <= 2

        # 测试向量检索
        vector_results = manager.query(source_name, "Python", mode="vector", top_k=2)
        assert len(vector_results) <= 2

        # 测试 BM25 检索
        bm25_results = manager.query(source_name, "Python", mode="bm25", top_k=2)
        assert len(bm25_results) <= 2

    def test_query_before_sync(self, manager, test_data_dir):
        """测试同步前查询应该失败"""
        source_name = "test_source"

        # 只添加，不同步
        config = SourceConfig(
            name=source_name,
            type=SourceType.LOCAL,
            path=str(test_data_dir)
        )
        manager.add_source(config)

        # 查询应该失败
        with pytest.raises(ValueError, match="索引尚未构建"):
            manager.query(source_name, "test")

    def test_query_nonexistent_source(self, manager):
        """测试查询不存在的数据源"""
        with pytest.raises(ValueError, match="不存在"):
            manager.query("nonexistent", "test")

    def test_sync_updates_source_info(self, manager, test_data_dir):
        """测试同步后更新数据源信息"""
        source_name = "test_source"

        # 添加数据源
        config = SourceConfig(
            name=source_name,
            type=SourceType.LOCAL,
            path=str(test_data_dir)
        )
        manager.add_source(config)

        # 同步前的信息
        info_before = manager.get_source_info(source_name)
        assert info_before.status == "未同步"
        assert info_before.raw_count == 0
        assert info_before.document_count == 0

        # 同步
        manager.sync_source(source_name)

        # 同步后的信息
        info_after = manager.get_source_info(source_name)
        assert info_after.status == "已同步"
        assert info_after.raw_count == 3
        assert info_after.document_count == 3
        assert info_after.last_sync is not None

    def test_resync_source(self, manager, test_data_dir):
        """测试重新同步数据源"""
        source_name = "test_source"

        # 添加并同步
        config = SourceConfig(
            name=source_name,
            type=SourceType.LOCAL,
            path=str(test_data_dir)
        )
        manager.add_source(config)
        result1 = manager.sync_source(source_name)

        # 再次同步（增量同步，没有新文件）
        result2 = manager.sync_source(source_name)

        # 增量同步时，第二次同步应该返回 0（没有新文件）
        assert result2.raw_count == 0
        assert result2.document_count == 0

        # 但总计数应该保持不变
        info = manager.get_source_info(source_name)
        assert info.raw_count == result1.raw_count
        assert info.document_count == result1.document_count

    def test_query_top_k(self, manager, test_data_dir):
        """测试 top_k 参数"""
        source_name = "test_source"

        # 添加并同步
        config = SourceConfig(
            name=source_name,
            type=SourceType.LOCAL,
            path=str(test_data_dir)
        )
        manager.add_source(config)
        manager.sync_source(source_name)

        # 测试不同的 top_k
        results_1 = manager.query(source_name, "Python", top_k=1)
        assert len(results_1) <= 1

        results_3 = manager.query(source_name, "Python", top_k=3)
        assert len(results_3) <= 3

        results_10 = manager.query(source_name, "Python", top_k=10)
        assert len(results_10) <= 10

    def test_query_results_format(self, manager, test_data_dir):
        """测试查询结果格式"""
        source_name = "test_source"

        # 添加并同步
        config = SourceConfig(
            name=source_name,
            type=SourceType.LOCAL,
            path=str(test_data_dir)
        )
        manager.add_source(config)
        manager.sync_source(source_name)

        # 查询
        results = manager.query(source_name, "Python", top_k=1)

        # 验证结果格式
        assert len(results) > 0
        result = results[0]

        assert "rank" in result
        assert "score" in result
        assert "text" in result
        assert "metadata" in result
        assert "node_id" in result

        assert isinstance(result["rank"], int)
        assert isinstance(result["score"], float)
        assert isinstance(result["text"], str)
        assert isinstance(result["metadata"], dict)
        assert isinstance(result["node_id"], str)

    def test_empty_query(self, manager, test_data_dir):
        """测试空查询"""
        source_name = "test_source"

        # 添加并同步
        config = SourceConfig(
            name=source_name,
            type=SourceType.LOCAL,
            path=str(test_data_dir)
        )
        manager.add_source(config)
        manager.sync_source(source_name)

        # 空查询应该返回结果（取决于检索器实现）
        results = manager.query(source_name, "", top_k=3)
        # 可能返回空或默认结果
        assert isinstance(results, list)
