"""数据模型定义

本模块定义了 DataSource 系统的核心数据模型。
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


# ============ 枚举类型 ============


class SourceType(str, Enum):
    """数据源类型"""

    JIRA = "jira"
    CONFLUENCE = "confluence"
    LOCAL = "local"


# ============ 配置模型 ============


class SourceConfig(BaseModel):
    """数据源配置（扁平化设计）

    所有类型的数据源共享同一个配置类，通过 type 字段区分。
    不同类型使用不同的字段组合。
    """

    name: str = Field(..., description="数据源名称（唯一标识）")
    type: SourceType = Field(..., description="数据源类型")

    # 连接配置
    server: Optional[str] = Field(None, description="服务器地址（Jira/Confluence）")
    path: Optional[str] = Field(None, description="本地路径（Local）")

    # 查询配置
    project: Optional[str] = Field(None, description="项目 key（Jira）")
    jql: Optional[str] = Field(None, description="JQL 查询语句（Jira）")
    space: Optional[str] = Field(None, description="空间 key（Confluence）")
    cql: Optional[str] = Field(None, description="CQL 查询语句（Confluence）")

    # 通用选项（使用字典存储其他配置）
    options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "download_attachments": True,
            "attachment_types": ["png", "jpg", "jpeg", "gif", "svg", "webp"],
            "max_attachment_size": None,
            "recursive": True,
            "file_types": ["pdf", "docx", "pptx", "xlsx", "md", "txt"],
        },
        description="其他配置选项"
    )

    # 元数据
    description: Optional[str] = Field(None, description="数据源描述")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    def to_yaml(self) -> str:
        """导出为 YAML 格式

        Returns:
            YAML 格式的配置字符串
        """
        import yaml
        data = self.model_dump()
        # 转换 datetime 为字符串
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        # 转换枚举为字符串
        data["type"] = data["type"].value if hasattr(data["type"], "value") else data["type"]
        return yaml.dump(data, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "SourceConfig":
        """从 YAML 加载配置

        Args:
            yaml_str: YAML 格式的配置字符串

        Returns:
            SourceConfig 实例
        """
        import yaml
        data = yaml.safe_load(yaml_str)
        # 转换字符串为 datetime
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


# ============ 同步结果 ============


class SyncResult(BaseModel):
    """同步结果

    记录一次同步操作的完整信息，包括统计数据和错误信息。
    """

    source_name: str = Field(..., description="数据源名称")
    status: str = Field(..., description="同步状态：success | partial | failed")
    started_at: datetime = Field(..., description="开始时间")
    completed_at: datetime = Field(..., description="完成时间")
    duration_seconds: float = Field(..., description="耗时（秒）")

    # 统计信息
    total_items: int = Field(0, description="总条目数")
    successful_items: int = Field(0, description="成功条目数")
    failed_items: int = Field(0, description="失败条目数")
    total_documents: int = Field(0, description="总文档数")
    total_assets: int = Field(0, description="总资源数（附件）")

    # 索引统计
    total_nodes: int = Field(0, description="索引节点数")
    index_size_mb: float = Field(0.0, description="索引大小（MB）")

    # 错误信息
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="错误列表，每个错误包含 item_id 和 error"
    )

    def to_markdown(self) -> str:
        """生成 Markdown 格式的同步报告

        Returns:
            Markdown 格式的报告字符串
        """
        status_emoji = {
            "success": "✅",
            "partial": "⚠️",
            "failed": "❌",
        }

        report = f"""# Sync Report: {self.source_name}

## Summary
- Status: {status_emoji.get(self.status, "❓")} {self.status}
- Duration: {self.duration_seconds:.2f}s
- Started: {self.started_at.strftime("%Y-%m-%d %H:%M:%S")}
- Completed: {self.completed_at.strftime("%Y-%m-%d %H:%M:%S")}

## Statistics
- Total items: {self.total_items}
- Successful: {self.successful_items}
- Failed: {self.failed_items}
- Documents: {self.total_documents}
- Assets: {self.total_assets}

## Index
- Nodes: {self.total_nodes}
- Size: {self.index_size_mb:.2f} MB

## Errors
{self._format_errors()}
"""
        return report

    def _format_errors(self) -> str:
        """格式化错误列表"""
        if not self.errors:
            return "No errors ✅"

        lines = []
        for i, error in enumerate(self.errors[:10], 1):  # 只显示前 10 个
            item_id = error.get("item_id", "unknown")
            error_msg = error.get("error", "unknown error")
            lines.append(f"{i}. **{item_id}**: {error_msg}")

        if len(self.errors) > 10:
            lines.append(f"\n... and {len(self.errors) - 10} more errors")

        return "\n".join(lines)


# ============ 数据源信息 ============


class SourceInfo(BaseModel):
    """数据源详细信息

    包含配置和运行时统计信息。
    """

    config: SourceConfig = Field(..., description="数据源配置")

    # 统计信息
    total_items: int = Field(0, description="总条目数")
    total_documents: int = Field(0, description="总文档数")
    total_assets: int = Field(0, description="总资源数")
    total_nodes: int = Field(0, description="索引节点数")
    index_size_mb: float = Field(0.0, description="索引大小（MB）")

    # 状态
    last_sync: Optional[datetime] = Field(None, description="最后同步时间")
    status: str = Field(
        "not_synced",
        description="状态：not_synced | syncing | ready | error"
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于显示）

        Returns:
            包含所有信息的字典
        """
        return {
            "name": self.config.name,
            "type": self.config.type.value,
            "server": self.config.server,
            "path": self.config.path,
            "description": self.config.description,
            "items": self.total_items,
            "documents": self.total_documents,
            "assets": self.total_assets,
            "nodes": self.total_nodes,
            "index_size_mb": round(self.index_size_mb, 2),
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "status": self.status,
        }
