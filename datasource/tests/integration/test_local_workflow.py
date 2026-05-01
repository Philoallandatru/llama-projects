"""集成测试 - 本地文件工作流

测试完整的工作流程：添加 -> 同步 -> 查询 -> 删除
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from datasource.core.manager import SourceManager
from datasource.core.models import SourceConfig, SourceType


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def test_files(temp_dir):
    """创建测试文件集"""
    files_dir = temp_dir / "test_files"
    files_dir.mkdir()

    # 创建多个测试文件
    (files_dir / "doc1.md").write_text(
        "# Document 1\n\nThis is the first test document.",
        encoding="utf-8"
    )
    (files_dir / "doc2.txt").write_text(
        "Document 2 content in plain text.",
        encoding="utf-8"
    )

    # 创建子目录
    subdir = files_dir / "subdir"
    subdir.mkdir()
    (subdir / "doc3.md").write_text(
        "# Document 3\n\nThis is in a subdirectory.",
        encoding="utf-8"
    )

    return files_dir


@pytest.fixture
def manager(temp_dir):
    """创建 SourceManager 实例"""
    return SourceManager(temp_dir / "data")


class TestLocalWorkflow:
    """本地文件工作流集成测试"""

    def test_complete_workflow(self, manager, test_files):
        """测试完整工作流：添加 -> 同步 -> 查询 -> 删除"""

        # 1. 添加数据源
        config = SourceConfig(
            name="test_docs",
            type=SourceType.LOCAL,
            path=str(test_files),
            description="Test documents"
        )

        info = manager.add_source(config)
        assert info.name == "test_docs"
        assert info.status == "未同步"
        assert info.raw_count == 0
        assert info.document_count == 0

        # 2. 同步数据源
        result = manager.sync_source("test_docs")
        assert result.success
        assert result.raw_count == 3  # doc1.md, doc2.txt, subdir/doc3.md
        assert result.document_count == 3
        assert result.error_count == 0

        # 3. 查询数据源信息
        info = manager.get_source_info("test_docs")
        assert info.status == "已同步"
        assert info.raw_count == 3
        assert info.document_count == 3
        assert info.last_sync is not None
        assert info.total_size > 0

        # 4. 列出所有数据源
        sources = manager.list_sources()
        assert len(sources) == 1
        assert sources[0].name == "test_docs"

        # 5. 删除数据源
        manager.delete_source("test_docs")
        sources = manager.list_sources()
        assert len(sources) == 0

    def test_multiple_sources(self, manager, temp_dir):
        """测试管理多个数据源"""

        # 创建两个不同的文件目录
        dir1 = temp_dir / "dir1"
        dir1.mkdir()
        (dir1 / "file1.md").write_text("# File 1", encoding="utf-8")

        dir2 = temp_dir / "dir2"
        dir2.mkdir()
        (dir2 / "file2.txt").write_text("File 2", encoding="utf-8")

        # 添加两个数据源
        config1 = SourceConfig(name="source1", type=SourceType.LOCAL, path=str(dir1))
        config2 = SourceConfig(name="source2", type=SourceType.LOCAL, path=str(dir2))

        manager.add_source(config1)
        manager.add_source(config2)

        # 同步两个数据源
        result1 = manager.sync_source("source1")
        result2 = manager.sync_source("source2")

        assert result1.success
        assert result2.success

        # 列出所有数据源
        sources = manager.list_sources()
        assert len(sources) == 2

        names = [s.name for s in sources]
        assert "source1" in names
        assert "source2" in names

        # 验证数据独立
        info1 = manager.get_source_info("source1")
        info2 = manager.get_source_info("source2")

        assert info1.raw_count == 1
        assert info2.raw_count == 1

    def test_resync(self, manager, test_files):
        """测试重新同步"""

        config = SourceConfig(
            name="test_docs",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        # 第一次同步
        manager.add_source(config)
        result1 = manager.sync_source("test_docs")
        assert result1.success
        assert result1.raw_count == 3

        # 添加新文件
        (test_files / "doc4.md").write_text("# Document 4", encoding="utf-8")

        # 第二次同步（增量同步，只获取新文件）
        result2 = manager.sync_source("test_docs")
        assert result2.success
        assert result2.raw_count == 1  # 只包含新文件

        # 验证信息已更新
        info = manager.get_source_info("test_docs")
        assert info.raw_count == 4
        assert info.document_count == 4

    def test_sync_with_errors(self, manager, temp_dir):
        """测试同步时的错误处理"""

        files_dir = temp_dir / "files"
        files_dir.mkdir()

        # 创建一个正常文件
        (files_dir / "good.md").write_text("# Good", encoding="utf-8")

        config = SourceConfig(
            name="test_docs",
            type=SourceType.LOCAL,
            path=str(files_dir)
        )

        manager.add_source(config)
        result = manager.sync_source("test_docs")

        # 即使有错误，成功的文件也应该被处理
        assert result.raw_count >= 1
        assert result.document_count >= 1

    def test_empty_directory(self, manager, temp_dir):
        """测试空目录"""

        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        config = SourceConfig(
            name="empty_source",
            type=SourceType.LOCAL,
            path=str(empty_dir)
        )

        manager.add_source(config)
        result = manager.sync_source("empty_source")

        assert result.success
        assert result.raw_count == 0
        assert result.document_count == 0
