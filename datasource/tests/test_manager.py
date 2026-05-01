"""SourceManager 单元测试"""

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
def manager(temp_dir):
    """创建 SourceManager 实例"""
    return SourceManager(temp_dir / "data")


@pytest.fixture
def test_files(temp_dir):
    """创建测试文件"""
    files_dir = temp_dir / "test_files"
    files_dir.mkdir()
    (files_dir / "test.md").write_text("# Test\n\nContent", encoding="utf-8")
    return files_dir


class TestSourceManager:
    """SourceManager 测试"""

    def test_init(self, temp_dir):
        """测试初始化"""
        manager = SourceManager(temp_dir / "data")
        assert manager.data_dir.exists()
        assert manager.paths is not None

    def test_add_source(self, manager, test_files):
        """测试添加数据源"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files),
            description="Test source"
        )

        info = manager.add_source(config)

        assert info.name == "test_source"
        assert info.type == SourceType.LOCAL
        assert info.config.path == str(test_files)
        assert info.status == "未同步"

        # 检查目录和配置文件已创建
        assert manager.paths.exists("test_source")
        assert manager.paths.source_config("test_source").exists()

    def test_add_source_duplicate(self, manager, test_files):
        """测试添加重复数据源"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        manager.add_source(config)

        # 再次添加应该失败
        with pytest.raises(ValueError, match="已存在"):
            manager.add_source(config)

    def test_list_sources_empty(self, manager):
        """测试列出空数据源列表"""
        sources = manager.list_sources()
        assert len(sources) == 0

    def test_list_sources(self, manager, test_files):
        """测试列出数据源"""
        # 添加两个数据源
        config1 = SourceConfig(name="source1", type=SourceType.LOCAL, path=str(test_files))
        config2 = SourceConfig(name="source2", type=SourceType.LOCAL, path=str(test_files))

        manager.add_source(config1)
        manager.add_source(config2)

        sources = manager.list_sources()
        assert len(sources) == 2

        names = [s.name for s in sources]
        assert "source1" in names
        assert "source2" in names

    def test_get_source_info(self, manager, test_files):
        """测试获取数据源信息"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files),
            description="Test description"
        )

        manager.add_source(config)
        info = manager.get_source_info("test_source")

        assert info.name == "test_source"
        assert info.type == SourceType.LOCAL
        assert info.config.description == "Test description"
        assert info.raw_count == 0
        assert info.document_count == 0
        assert info.status == "未同步"

    def test_get_source_info_not_found(self, manager):
        """测试获取不存在的数据源"""
        with pytest.raises(ValueError, match="不存在"):
            manager.get_source_info("nonexistent")

    def test_delete_source(self, manager, test_files):
        """测试删除数据源"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        manager.add_source(config)
        assert manager.paths.exists("test_source")

        manager.delete_source("test_source")
        assert not manager.paths.exists("test_source")

    def test_delete_source_not_found(self, manager):
        """测试删除不存在的数据源"""
        with pytest.raises(ValueError, match="不存在"):
            manager.delete_source("nonexistent")

    def test_sync_source(self, manager, test_files):
        """测试同步数据源"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        manager.add_source(config)
        result = manager.sync_source("test_source")

        assert result.raw_count > 0
        assert result.document_count > 0
        assert result.success

        # 检查数据已保存
        info = manager.get_source_info("test_source")
        assert info.raw_count > 0
        assert info.document_count > 0
        assert info.status == "已同步"
        assert info.last_sync is not None

    def test_sync_source_not_found(self, manager):
        """测试同步不存在的数据源"""
        with pytest.raises(ValueError, match="不存在"):
            manager.sync_source("nonexistent")

    def test_create_source_local(self, manager, test_files):
        """测试创建本地数据源实例"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        source = manager._create_source(config)
        assert source is not None
        assert source.config == config

    def test_create_source_jira_requires_token(self, manager):
        """测试创建 Jira 数据源需要 token"""
        config = SourceConfig(
            name="test",
            type=SourceType.JIRA,
            server="https://jira.example.com"
        )

        with pytest.raises(ValueError, match="token"):
            manager._create_source(config)

    def test_create_source_confluence(self, manager):
        """测试创建 Confluence 数据源"""
        config = SourceConfig(
            name="test",
            type=SourceType.CONFLUENCE,
            server="https://confluence.example.com",
            options={"token": "test_token"}
        )

        source = manager._create_source(config)
        assert source is not None
        assert source.server == "https://confluence.example.com"

    def test_create_source_confluence_missing_token(self, manager):
        """测试创建 Confluence 数据源缺少 token"""
        config = SourceConfig(
            name="test",
            type=SourceType.CONFLUENCE,
            server="https://confluence.example.com"
        )

        with pytest.raises(ValueError, match="必须在 options 中指定 token"):
            manager._create_source(config)
