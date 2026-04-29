"""单元测试：路径管理

测试 paths.py 中的 Paths 类。
"""

import pytest
from pathlib import Path
from datasource.core.paths import Paths


class TestPaths:
    """测试 Paths 类"""

    @pytest.fixture
    def temp_paths(self, tmp_path):
        """创建临时路径管理器"""
        return Paths(base_dir=tmp_path)

    def test_init_default(self):
        """测试默认初始化"""
        paths = Paths()
        assert paths.base_dir.name == "data"
        assert paths.sources_dir == paths.base_dir / "sources"
        assert paths.logs_dir == paths.base_dir / "logs"

    def test_init_custom(self, tmp_path):
        """测试自定义基础目录"""
        paths = Paths(base_dir=tmp_path)
        assert paths.base_dir == tmp_path
        assert paths.sources_dir == tmp_path / "sources"
        assert paths.logs_dir == tmp_path / "logs"

    def test_source(self, temp_paths):
        """测试数据源根目录"""
        source_dir = temp_paths.source("test_source")
        assert source_dir == temp_paths.sources_dir / "test_source"
        assert source_dir.name == "test_source"

    def test_source_config(self, temp_paths):
        """测试配置文件路径"""
        config_file = temp_paths.source_config("test_source")
        assert config_file == temp_paths.sources_dir / "test_source" / "source.yaml"
        assert config_file.name == "source.yaml"

    def test_raw(self, temp_paths):
        """测试原始数据目录"""
        raw_dir = temp_paths.raw("test_source")
        assert raw_dir == temp_paths.sources_dir / "test_source" / "raw"
        assert raw_dir.name == "raw"

    def test_documents(self, temp_paths):
        """测试文档目录"""
        docs_dir = temp_paths.documents("test_source")
        assert docs_dir == temp_paths.sources_dir / "test_source" / "documents"
        assert docs_dir.name == "documents"

    def test_assets(self, temp_paths):
        """测试资源目录"""
        assets_dir = temp_paths.assets("test_source")
        assert assets_dir == temp_paths.sources_dir / "test_source" / "assets"
        assert assets_dir.name == "assets"

    def test_indexes(self, temp_paths):
        """测试索引根目录"""
        indexes_dir = temp_paths.indexes("test_source")
        assert indexes_dir == temp_paths.sources_dir / "test_source" / "indexes"
        assert indexes_dir.name == "indexes"

    def test_vector_index(self, temp_paths):
        """测试向量索引目录"""
        vector_dir = temp_paths.vector_index("test_source")
        assert vector_dir == temp_paths.sources_dir / "test_source" / "indexes" / "vector"
        assert vector_dir.name == "vector"

    def test_bm25_index(self, temp_paths):
        """测试 BM25 索引文件"""
        bm25_file = temp_paths.bm25_index("test_source")
        assert bm25_file == temp_paths.sources_dir / "test_source" / "indexes" / "bm25.pkl"
        assert bm25_file.name == "bm25.pkl"

    def test_manifest(self, temp_paths):
        """测试清单文件"""
        manifest_file = temp_paths.manifest("test_source")
        assert manifest_file == temp_paths.sources_dir / "test_source" / "manifest.json"
        assert manifest_file.name == "manifest.json"

    def test_sync_log(self, temp_paths):
        """测试同步日志文件"""
        log_file = temp_paths.sync_log("test_source")
        assert log_file == temp_paths.sources_dir / "test_source" / "sync.log"
        assert log_file.name == "sync.log"

    def test_sync_report(self, temp_paths):
        """测试同步报告文件"""
        report_file = temp_paths.sync_report("test_source")
        assert report_file == temp_paths.sources_dir / "test_source" / "sync_report.md"
        assert report_file.name == "sync_report.md"

    def test_ensure_dirs(self, temp_paths):
        """测试创建目录"""
        temp_paths.ensure_dirs("test_source")

        # 验证所有目录都已创建
        assert temp_paths.source("test_source").exists()
        assert temp_paths.raw("test_source").exists()
        assert temp_paths.documents("test_source").exists()
        assert temp_paths.assets("test_source").exists()
        assert temp_paths.indexes("test_source").exists()
        assert temp_paths.vector_index("test_source").exists()
        assert temp_paths.logs_dir.exists()

    def test_ensure_dirs_idempotent(self, temp_paths):
        """测试重复创建目录（幂等性）"""
        temp_paths.ensure_dirs("test_source")
        temp_paths.ensure_dirs("test_source")  # 第二次调用不应报错

        assert temp_paths.source("test_source").exists()

    def test_exists(self, temp_paths):
        """测试检查数据源是否存在"""
        assert not temp_paths.exists("test_source")

        temp_paths.ensure_dirs("test_source")
        assert temp_paths.exists("test_source")

    def test_list_sources_empty(self, temp_paths):
        """测试列出空数据源列表"""
        sources = temp_paths.list_sources()
        assert sources == []

    def test_list_sources(self, temp_paths):
        """测试列出数据源"""
        # 创建几个数据源
        for name in ["source1", "source2", "source3"]:
            temp_paths.ensure_dirs(name)
            config_file = temp_paths.source_config(name)
            config_file.write_text("name: " + name)

        sources = temp_paths.list_sources()
        assert len(sources) == 3
        assert "source1" in sources
        assert "source2" in sources
        assert "source3" in sources
        assert sources == sorted(sources)  # 应该是排序的

    def test_list_sources_ignores_incomplete(self, temp_paths):
        """测试忽略不完整的数据源（没有 source.yaml）"""
        # 创建目录但不创建配置文件
        temp_paths.ensure_dirs("incomplete")

        # 创建完整的数据源
        temp_paths.ensure_dirs("complete")
        temp_paths.source_config("complete").write_text("name: complete")

        sources = temp_paths.list_sources()
        assert len(sources) == 1
        assert "complete" in sources
        assert "incomplete" not in sources

    def test_get_size_mb_empty(self, temp_paths):
        """测试计算空目录大小"""
        temp_paths.ensure_dirs("test_source")
        size = temp_paths.get_size_mb("test_source")
        assert size == 0.0

    def test_get_size_mb_nonexistent(self, temp_paths):
        """测试计算不存在目录的大小"""
        size = temp_paths.get_size_mb("nonexistent")
        assert size == 0.0

    def test_get_size_mb(self, temp_paths):
        """测试计算目录大小"""
        temp_paths.ensure_dirs("test_source")

        # 创建一些文件
        (temp_paths.raw("test_source") / "file1.json").write_text("x" * 1024)  # 1 KB
        (temp_paths.documents("test_source") / "file2.json").write_text("x" * 2048)  # 2 KB

        size = temp_paths.get_size_mb("test_source")
        assert size > 0
        assert size < 1  # 应该小于 1 MB

    def test_get_index_size_mb_empty(self, temp_paths):
        """测试计算空索引大小"""
        temp_paths.ensure_dirs("test_source")
        size = temp_paths.get_index_size_mb("test_source")
        assert size == 0.0

    def test_get_index_size_mb_nonexistent(self, temp_paths):
        """测试计算不存在索引的大小"""
        size = temp_paths.get_index_size_mb("nonexistent")
        assert size == 0.0

    def test_get_index_size_mb(self, temp_paths):
        """测试计算索引大小"""
        temp_paths.ensure_dirs("test_source")

        # 创建索引文件
        (temp_paths.vector_index("test_source") / "index.json").write_text("x" * 1024)
        temp_paths.bm25_index("test_source").write_text("x" * 2048)

        size = temp_paths.get_index_size_mb("test_source")
        assert size > 0
        assert size < 1  # 应该小于 1 MB

    def test_multiple_sources(self, temp_paths):
        """测试多个数据源互不干扰"""
        temp_paths.ensure_dirs("source1")
        temp_paths.ensure_dirs("source2")

        # 在不同数据源中创建文件
        (temp_paths.raw("source1") / "file1.json").write_text("source1")
        (temp_paths.raw("source2") / "file2.json").write_text("source2")

        # 验证文件在正确的位置
        assert (temp_paths.raw("source1") / "file1.json").exists()
        assert (temp_paths.raw("source2") / "file2.json").exists()
        assert not (temp_paths.raw("source1") / "file2.json").exists()
        assert not (temp_paths.raw("source2") / "file1.json").exists()
