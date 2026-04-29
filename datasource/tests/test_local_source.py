"""LocalDataSource 单元测试"""

import pytest
from pathlib import Path
import tempfile
import shutil

from datasource.core.sources.local import LocalDataSource
from datasource.core.models import SourceConfig, SourceType


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def test_files(temp_dir):
    """创建测试文件"""
    # 创建测试文件
    (temp_dir / "test1.md").write_text("# Test 1\n\nContent 1", encoding="utf-8")
    (temp_dir / "test2.txt").write_text("Test 2 content", encoding="utf-8")

    # 创建子目录
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "test3.md").write_text("# Test 3\n\nContent 3", encoding="utf-8")

    # 创建不支持的文件（应该被忽略）
    (temp_dir / "test.py").write_text("print('hello')", encoding="utf-8")

    return temp_dir


@pytest.fixture
def local_config(test_files):
    """创建本地数据源配置"""
    return SourceConfig(
        name="test_local",
        type=SourceType.LOCAL,
        path=str(test_files),
        description="Test local source"
    )


class TestLocalDataSource:
    """LocalDataSource 测试"""

    def test_init_valid_path(self, local_config):
        """测试初始化 - 有效路径"""
        source = LocalDataSource(local_config)
        assert source.config == local_config
        assert source.root_path.exists()

    def test_init_invalid_path(self):
        """测试初始化 - 无效路径"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/nonexistent/path"
        )
        with pytest.raises(ValueError, match="Path does not exist"):
            LocalDataSource(config)

    def test_init_path_is_file(self, temp_dir):
        """测试初始化 - 路径是文件而非目录"""
        file_path = temp_dir / "file.txt"
        file_path.write_text("test", encoding="utf-8")

        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path=str(file_path)
        )
        with pytest.raises(ValueError, match="Path is not a directory"):
            LocalDataSource(config)

    def test_fetch_raw(self, local_config, temp_dir):
        """测试抓取原始数据"""
        source = LocalDataSource(local_config)
        output_dir = temp_dir / "output"

        items = list(source.fetch_raw(output_dir))

        # 应该找到 3 个支持的文件（test1.md, test2.txt, subdir/test3.md）
        assert len(items) == 3

        # 检查返回的数据
        item_ids = [item_id for item_id, _ in items]
        assert "test1" in item_ids
        assert "test2" in item_ids
        assert "subdir/test3" in item_ids

        # 检查 JSON 文件已保存
        assert (output_dir / "test1.json").exists()
        assert (output_dir / "test2.json").exists()

        # 检查原始数据内容
        for item_id, raw_data in items:
            assert raw_data['item_id'] == item_id
            assert 'file_path' in raw_data
            assert 'file_name' in raw_data
            assert 'file_size' in raw_data
            assert 'modified_time' in raw_data

    def test_fetch_raw_empty_directory(self, temp_dir):
        """测试抓取空目录"""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path=str(empty_dir)
        )
        source = LocalDataSource(config)
        output_dir = temp_dir / "output"

        items = list(source.fetch_raw(output_dir))
        assert len(items) == 0

    def test_build_document(self, local_config, test_files, temp_dir):
        """测试构建文档"""
        source = LocalDataSource(local_config)

        # 准备原始数据
        file_path = test_files / "test1.md"
        stat = file_path.stat()
        raw_data = {
            'item_id': 'test1',
            'file_path': str(file_path),
            'relative_path': 'test1.md',
            'file_name': 'test1.md',
            'file_size': stat.st_size,
            'modified_time': '2024-01-01T00:00:00',
            'created_time': '2024-01-01T00:00:00',
            'extension': '.md',
        }

        assets_dir = temp_dir / "assets"
        doc = source.build_document('test1', raw_data, assets_dir)

        # 检查文档内容
        assert doc.text is not None
        assert len(doc.text) > 0

        # 检查 metadata
        assert doc.metadata['source_name'] == 'test_local'
        assert doc.metadata['source_type'] == 'local'
        assert doc.metadata['item_id'] == 'test1'
        assert doc.metadata['file_name'] == 'test1.md'
        assert doc.metadata['extension'] == '.md'

    def test_build_document_file_not_found(self, local_config, temp_dir):
        """测试构建文档 - 文件不存在"""
        source = LocalDataSource(local_config)

        raw_data = {
            'item_id': 'nonexistent',
            'file_path': '/nonexistent/file.txt',
            'relative_path': 'file.txt',
            'file_name': 'file.txt',
            'file_size': 0,
            'modified_time': '2024-01-01T00:00:00',
            'created_time': '2024-01-01T00:00:00',
            'extension': '.txt',
        }

        assets_dir = temp_dir / "assets"

        with pytest.raises(ValueError, match="File not found"):
            source.build_document('nonexistent', raw_data, assets_dir)

    def test_supported_extensions(self):
        """测试支持的文件扩展名"""
        expected = {'.pdf', '.docx', '.doc', '.md', '.txt', '.xlsx', '.xls', '.pptx', '.ppt'}
        assert LocalDataSource.SUPPORTED_EXTENSIONS == expected
