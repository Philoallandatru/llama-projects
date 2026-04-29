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
        result = SyncResult(
            success=True,
            raw_count=100,
            document_count=95,
            error_count=5,
            errors=["Error 1", "Error 2"]
        )

        assert result.success is True
        assert result.raw_count == 100
        assert result.document_count == 95
        assert result.error_count == 5
        assert len(result.errors) == 2

    def test_default_statistics(self):
        """测试默认统计值"""
        result = SyncResult(
            success=True
        )

        assert result.raw_count == 0
        assert result.document_count == 0
        assert result.error_count == 0
        assert result.errors == []

    def test_with_errors(self):
        """测试带错误信息"""
        errors = ["Error 1", "Error 2", "Error 3"]

        result = SyncResult(
            success=False,
            raw_count=10,
            document_count=7,
            error_count=3,
            errors=errors
        )

        assert result.success is False
        assert result.error_count == 3
        assert len(result.errors) == 3
        assert result.errors[0] == "Error 1"


class TestSourceInfo:
    """测试 SourceInfo 数据模型"""

    def test_create_source_info(self):
        """测试创建数据源信息"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp"
        )

        info = SourceInfo(
            name="test",
            type=SourceType.LOCAL,
            config=config
        )

        assert info.name == "test"
        assert info.type == SourceType.LOCAL
        assert info.config == config
        assert info.raw_count == 0
        assert info.document_count == 0
        assert info.total_size == 0.0
        assert info.last_sync is None
        assert info.status == "未同步"

    def test_with_statistics(self):
        """测试带统计信息"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp"
        )

        info = SourceInfo(
            name="test",
            type=SourceType.LOCAL,
            config=config,
            raw_count=100,
            document_count=95,
            total_size=10.5,
            last_sync="2026-04-29T10:00:00",
            status="已同步"
        )

        assert info.raw_count == 100
        assert info.document_count == 95
        assert info.total_size == 10.5
        assert info.last_sync == "2026-04-29T10:00:00"
        assert info.status == "已同步"

    def test_to_dict(self):
        """测试转换为字典"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp",
            description="Test"
        )

        info = SourceInfo(
            name="test",
            type=SourceType.LOCAL,
            config=config,
            raw_count=100,
            document_count=95,
            total_size=10.567,
            last_sync="2024-01-01T10:00:00",
            status="已同步"
        )

        data = info.to_dict()

        assert data["name"] == "test"
        assert data["type"] == "local"
        assert data["path"] == "/tmp"
        assert data["description"] == "Test"
        assert data["raw_count"] == 100
        assert data["document_count"] == 95
        assert data["total_size_mb"] == 10.57
        assert data["last_sync"] == "2024-01-01T10:00:00"
        assert data["status"] == "已同步"

    def test_to_dict_no_sync(self):
        """测试未同步的数据源"""
        config = SourceConfig(
            name="test",
            type=SourceType.LOCAL,
            path="/tmp"
        )

        info = SourceInfo(
            name="test",
            type=SourceType.LOCAL,
            config=config
        )
        data = info.to_dict()

        assert data["last_sync"] is None
        assert data["status"] == "未同步"
