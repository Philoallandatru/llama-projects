"""单元测试：数据模型

测试 models.py 中的所有数据模型类。
"""

import pytest
from datetime import datetime
from datasource.core.models import (
    SourceType,
    SourceConfig,
    SyncResult,
    SourceInfo,
)


class TestSourceType:
    """测试 SourceType 枚举"""

    def test_source_types(self):
        """测试所有数据源类型"""
        assert SourceType.JIRA == "jira"
        assert SourceType.CONFLUENCE == "confluence"
        assert SourceType.LOCAL == "local"

    def test_source_type_values(self):
        """测试枚举值列表"""
        types = [t.value for t in SourceType]
        assert "jira" in types
        assert "confluence" in types
        assert "local" in types


class TestSourceConfig:
    """测试 SourceConfig 数据模型"""

    def test_create_jira_config(self):
        """测试创建 Jira 配置"""
        config = SourceConfig(
            name="test_jira",
            type=SourceType.JIRA,
            server="https://jira.example.com",
            project="TEST",
            jql="project = TEST"
        )

        assert config.name == "test_jira"
        assert config.type == SourceType.JIRA
        assert config.server == "https://jira.example.com"
        assert config.project == "TEST"
        assert config.jql == "project = TEST"
        assert config.path is None

    def test_create_local_config(self):
        """测试创建本地文件配置"""
        config = SourceConfig(
            name="test_local",
            type=SourceType.LOCAL,
            path="/path/to/docs"
        )

        assert config.name == "test_local"
        assert config.type == SourceType.LOCAL
        assert config.path == "/path/to/docs"
        assert config.server is None

    def test_default_options(self):
        """测试默认选项"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp"
        )

        assert config.options["download_attachments"] is True
        assert "png" in config.options["attachment_types"]
        assert config.options["recursive"] is True

    def test_custom_options(self):
        """测试自定义选项"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp",
            options={"custom_key": "custom_value"}
        )

        assert config.options["custom_key"] == "custom_value"

    def test_metadata_fields(self):
        """测试元数据字段"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp",
            description="Test description",
            tags=["tag1", "tag2"]
        )

        assert config.description == "Test description"
        assert config.tags == ["tag1", "tag2"]
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)

    def test_to_yaml(self):
        """测试导出为 YAML"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp"
        )

        yaml_str = config.to_yaml()
        assert "name: test" in yaml_str
        assert "type: local" in yaml_str
        assert "path: /tmp" in yaml_str

    def test_from_yaml(self):
        """测试从 YAML 加载"""
        yaml_str = """
name: test
type: local
path: /tmp
description: Test
tags:
  - tag1
  - tag2
created_at: '2024-01-01T10:00:00'
updated_at: '2024-01-01T10:00:00'
options:
  download_attachments: true
"""
        config = SourceConfig.from_yaml(yaml_str)

        assert config.name == "test"
        assert config.type == SourceType.LOCAL
        assert config.path == "/tmp"
        assert config.description == "Test"
        assert config.tags == ["tag1", "tag2"]

    def test_yaml_roundtrip(self):
        """测试 YAML 序列化往返"""
        original = SourceConfig(
            name="test",
            type=SourceType.JIRA,
            server="https://jira.example.com",
            project="TEST"
        )

        yaml_str = original.to_yaml()
        restored = SourceConfig.from_yaml(yaml_str)

        assert restored.name == original.name
        assert restored.type == original.type
        assert restored.server == original.server
        assert restored.project == original.project


class TestSyncResult:
    """测试 SyncResult 数据模型"""

    def test_create_sync_result(self):
        """测试创建同步结果"""
        started = datetime.now()
        completed = datetime.now()

        result = SyncResult(
            source_name="test",
            status="success",
            started_at=started,
            completed_at=completed,
            duration_seconds=10.5
        )

        assert result.source_name == "test"
        assert result.status == "success"
        assert result.started_at == started
        assert result.completed_at == completed
        assert result.duration_seconds == 10.5

    def test_default_statistics(self):
        """测试默认统计值"""
        result = SyncResult(
            source_name="test",
            status="success",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=0
        )

        assert result.total_items == 0
        assert result.successful_items == 0
        assert result.failed_items == 0
        assert result.total_documents == 0
        assert result.total_assets == 0
        assert result.total_nodes == 0
        assert result.index_size_mb == 0.0
        assert result.errors == []

    def test_with_statistics(self):
        """测试带统计信息"""
        result = SyncResult(
            source_name="test",
            status="partial",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=60.0,
            total_items=100,
            successful_items=95,
            failed_items=5,
            total_documents=95,
            total_assets=50,
            total_nodes=500,
            index_size_mb=10.5
        )

        assert result.total_items == 100
        assert result.successful_items == 95
        assert result.failed_items == 5
        assert result.total_documents == 95
        assert result.total_assets == 50
        assert result.total_nodes == 500
        assert result.index_size_mb == 10.5

    def test_with_errors(self):
        """测试带错误信息"""
        errors = [
            {"item_id": "item1", "error": "Error 1"},
            {"item_id": "item2", "error": "Error 2"},
        ]

        result = SyncResult(
            source_name="test",
            status="failed",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=5.0,
            errors=errors
        )

        assert len(result.errors) == 2
        assert result.errors[0]["item_id"] == "item1"
        assert result.errors[1]["error"] == "Error 2"

    def test_to_markdown(self):
        """测试生成 Markdown 报告"""
        result = SyncResult(
            source_name="test",
            status="success",
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            completed_at=datetime(2024, 1, 1, 10, 5, 0),
            duration_seconds=300.0,
            total_items=100,
            successful_items=100,
            total_nodes=500,
            index_size_mb=10.5
        )

        markdown = result.to_markdown()

        assert "# Sync Report: test" in markdown
        assert "✅ success" in markdown
        assert "Duration: 300.00s" in markdown
        assert "Total items: 100" in markdown
        assert "Nodes: 500" in markdown
        assert "Size: 10.50 MB" in markdown
        assert "No errors ✅" in markdown

    def test_markdown_with_errors(self):
        """测试带错误的 Markdown 报告"""
        errors = [{"item_id": f"item{i}", "error": f"Error {i}"} for i in range(15)]

        result = SyncResult(
            source_name="test",
            status="partial",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=10.0,
            errors=errors
        )

        markdown = result.to_markdown()

        assert "⚠️ partial" in markdown
        assert "item0" in markdown
        assert "item9" in markdown
        assert "and 5 more errors" in markdown  # 只显示前 10 个


class TestSourceInfo:
    """测试 SourceInfo 数据模型"""

    def test_create_source_info(self):
        """测试创建数据源信息"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp"
        )

        info = SourceInfo(config=config)

        assert info.config.name == "test"
        assert info.total_items == 0
        assert info.status == "not_synced"
        assert info.last_sync is None

    def test_with_statistics(self):
        """测试带统计信息"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp"
        )

        last_sync = datetime.now()

        info = SourceInfo(
            config=config,
            total_items=100,
            total_documents=100,
            total_assets=50,
            total_nodes=500,
            index_size_mb=10.5,
            last_sync=last_sync,
            status="ready"
        )

        assert info.total_items == 100
        assert info.total_documents == 100
        assert info.total_assets == 50
        assert info.total_nodes == 500
        assert info.index_size_mb == 10.5
        assert info.last_sync == last_sync
        assert info.status == "ready"

    def test_to_dict(self):
        """测试转换为字典"""
        config = SourceConfig(
            name="test",
            type=SourceType.JIRA,
            server="https://jira.example.com",
            description="Test Jira"
        )

        last_sync = datetime(2024, 1, 1, 10, 0, 0)

        info = SourceInfo(
            config=config,
            total_items=100,
            total_nodes=500,
            index_size_mb=10.567,
            last_sync=last_sync,
            status="ready"
        )

        data = info.to_dict()

        assert data["name"] == "test"
        assert data["type"] == "jira"
        assert data["server"] == "https://jira.example.com"
        assert data["description"] == "Test Jira"
        assert data["items"] == 100
        assert data["nodes"] == 500
        assert data["index_size_mb"] == 10.57  # 四舍五入到 2 位
        assert data["last_sync"] == "2024-01-01T10:00:00"
        assert data["status"] == "ready"

    def test_to_dict_no_sync(self):
        """测试未同步的数据源"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp"
        )

        info = SourceInfo(config=config)
        data = info.to_dict()

        assert data["last_sync"] is None
        assert data["status"] == "not_synced"
