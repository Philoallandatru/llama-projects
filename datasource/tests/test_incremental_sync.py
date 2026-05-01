"""测试增量同步功能"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from datasource.core.manager import SourceManager
from datasource.core.models import SourceConfig, SourceType
from datasource.core.sources.local import LocalDataSource


class TestIncrementalSync:
    """测试增量同步功能"""

    @pytest.fixture
    def manager(self, tmp_path):
        """创建 SourceManager"""
        return SourceManager(tmp_path)

    @pytest.fixture
    def test_files(self, tmp_path):
        """创建测试文件"""
        files_dir = tmp_path / "test_files"
        files_dir.mkdir()

        # 创建初始文件
        (files_dir / "doc1.md").write_text("# Document 1", encoding="utf-8")
        (files_dir / "doc2.md").write_text("# Document 2", encoding="utf-8")
        (files_dir / "doc3.txt").write_text("Document 3", encoding="utf-8")

        return files_dir

    def test_incremental_sync_no_changes(self, manager, test_files):
        """测试增量同步：没有变化"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        # 第一次同步
        manager.add_source(config)
        result1 = manager.sync_source("test_source")
        assert result1.success
        assert result1.raw_count == 3

        # 第二次同步（增量，没有变化）
        result2 = manager.sync_source("test_source", full=False)
        assert result2.success
        assert result2.raw_count == 0  # 没有新文件

        # 验证总计数保持不变
        info = manager.get_source_info("test_source")
        assert info.raw_count == 3

    def test_incremental_sync_new_files(self, manager, test_files):
        """测试增量同步：添加新文件"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        # 第一次同步
        manager.add_source(config)
        result1 = manager.sync_source("test_source")
        assert result1.success
        assert result1.raw_count == 3

        # 等待一小段时间确保时间戳不同
        time.sleep(0.1)

        # 添加新文件
        (test_files / "doc4.md").write_text("# Document 4", encoding="utf-8")
        (test_files / "doc5.txt").write_text("Document 5", encoding="utf-8")

        # 第二次同步（增量）
        result2 = manager.sync_source("test_source")
        assert result2.success
        assert result2.raw_count == 2  # 2 个新文件

        # 验证总计数更新
        info = manager.get_source_info("test_source")
        assert info.raw_count == 5

    def test_incremental_sync_modified_files(self, manager, test_files):
        """测试增量同步：修改现有文件"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        # 第一次同步
        manager.add_source(config)
        result1 = manager.sync_source("test_source")
        assert result1.success
        assert result1.raw_count == 3

        # 等待一小段时间
        time.sleep(0.1)

        # 修改现有文件
        (test_files / "doc1.md").write_text("# Document 1 - Updated", encoding="utf-8")

        # 第二次同步（增量）
        result2 = manager.sync_source("test_source")
        assert result2.success
        assert result2.raw_count == 1  # 1 个修改的文件

    def test_full_sync_vs_incremental(self, manager, test_files):
        """测试全量同步 vs 增量同步"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        # 第一次同步
        manager.add_source(config)
        result1 = manager.sync_source("test_source")
        assert result1.success
        assert result1.raw_count == 3

        # 增量同步（没有变化）
        result2 = manager.sync_source("test_source")
        assert result2.success
        assert result2.raw_count == 0

        # 全量同步（强制重新抓取所有文件）
        result3 = manager.sync_source("test_source", full=True)
        assert result3.success
        assert result3.raw_count == 3  # 重新抓取所有文件

    def test_incremental_sync_with_since_parameter(self, test_files, tmp_path):
        """测试 fetch_raw 的 since 参数"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        source = LocalDataSource(config)

        # 等待一小段时间，确保旧文件的时间戳稳定
        time.sleep(0.1)

        # 记录当前时间（在旧文件之后）
        now = datetime.now()

        # 再等待一小段时间
        time.sleep(0.1)

        # 添加新文件
        (test_files / "new_file.md").write_text("# New File", encoding="utf-8")

        # 使用 since 参数抓取（应该只获取新文件）
        results = list(source.fetch_raw(tmp_path, since=now.isoformat()))
        assert len(results) == 1

        # 不使用 since 参数（应该获取所有文件）
        results_all = list(source.fetch_raw(tmp_path))
        assert len(results_all) == 4  # 3 个原始文件 + 1 个新文件

    def test_incremental_sync_manifest_update(self, manager, test_files):
        """测试增量同步更新 manifest"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        # 第一次同步
        manager.add_source(config)
        result1 = manager.sync_source("test_source")
        assert result1.success

        # 读取 manifest
        manifest_path = manager.paths.manifest("test_source")
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest1 = json.load(f)

        assert 'last_sync' in manifest1
        last_sync1 = manifest1['last_sync']

        # 等待一小段时间
        time.sleep(0.1)

        # 第二次同步
        result2 = manager.sync_source("test_source")
        assert result2.success

        # 读取更新后的 manifest
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest2 = json.load(f)

        assert 'last_sync' in manifest2
        last_sync2 = manifest2['last_sync']

        # 验证 last_sync 已更新
        assert last_sync2 > last_sync1

    def test_incremental_sync_with_deleted_files(self, manager, test_files):
        """测试增量同步：删除文件（增量同步不会删除索引中的旧文件）"""
        config = SourceConfig(
            name="test_source",
            type=SourceType.LOCAL,
            path=str(test_files)
        )

        # 第一次同步
        manager.add_source(config)
        result1 = manager.sync_source("test_source")
        assert result1.success
        assert result1.raw_count == 3

        # 删除一个文件
        (test_files / "doc1.md").unlink()

        # 第二次同步（增量）
        result2 = manager.sync_source("test_source")
        assert result2.success
        assert result2.raw_count == 0  # 没有新文件

        # 注意：增量同步不会删除已索引的文件
        # 当前实现不会自动清理已删除的文件
        info = manager.get_source_info("test_source")
        # raw_count 仍然是 3，因为旧的 raw 文件还在
        assert info.raw_count == 3

        # 全量同步也不会自动清理旧文件（只是重新抓取）
        # 如果需要清理，应该先删除数据源再重新添加
        result3 = manager.sync_source("test_source", full=True)
        assert result3.success
        assert result3.raw_count == 2  # 只抓取了 2 个文件

        # 但是旧的 raw 文件仍然存在，所以 raw_count 仍然是 3
        # 这是当前实现的限制
        info = manager.get_source_info("test_source")
        # TODO: 未来可以实现清理逻辑
        assert info.raw_count >= 2  # 至少有 2 个文件
