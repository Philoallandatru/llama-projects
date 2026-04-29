"""
统一的数据模型定义

所有数据源都转换为这些标准模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """数据源类型"""
    JIRA = "jira"
    CONFLUENCE = "confluence"
    EXCEL = "excel"
    WORD = "word"
    POWERPOINT = "powerpoint"
    MARKDOWN = "markdown"
    PDF = "pdf"
    TEXT = "text"
    IMAGE = "image"


class DocumentStatus(str, Enum):
    """文档状态"""
    RAW = "raw"              # 原始数据
    PROCESSED = "processed"  # 已处理
    VALIDATED = "validated"  # 已验证
    INDEXED = "indexed"      # 已索引
    ERROR = "error"          # 错误


class UnifiedDocument(BaseModel):
    """统一的文档模型"""

    # 基本信息
    id: str = Field(..., description="唯一标识符")
    content: str = Field(..., description="文本内容")
    title: Optional[str] = Field(None, description="文档标题")

    # 来源信息
    source_type: SourceType = Field(..., description="数据源类型")
    source_id: str = Field(..., description="原始数据源ID")
    source_url: Optional[str] = Field(None, description="原始数据源URL")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    author: Optional[str] = Field(None, description="作者")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    # 处理信息
    status: DocumentStatus = Field(default=DocumentStatus.RAW, description="文档状态")
    processed_at: Optional[datetime] = Field(None, description="处理时间")

    # 向量嵌入
    embeddings: Optional[List[float]] = Field(None, description="向量嵌入")

    # 数据治理
    quality_score: Optional[float] = Field(None, description="质量分数 0-1")
    governance_tags: List[str] = Field(default_factory=list, description="治理标签")
    access_level: str = Field(default="public", description="访问级别")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "jira-PROJ-123",
                "content": "这是一个Jira问题的描述...",
                "title": "实现用户登录功能",
                "source_type": "jira",
                "source_id": "PROJ-123",
                "source_url": "https://your-domain.atlassian.net/browse/PROJ-123",
                "metadata": {
                    "project": "PROJ",
                    "issue_type": "Story",
                    "status": "In Progress",
                    "priority": "High"
                },
                "author": "zhang.san@example.com",
                "created_at": "2024-01-01T10:00:00Z",
                "status": "processed",
                "quality_score": 0.95,
                "access_level": "internal"
            }
        }


class RawDocument(BaseModel):
    """原始文档模型（从数据源获取的原始数据）"""

    source_type: SourceType
    source_id: str
    raw_data: Any  # 原始数据，可以是任何格式
    metadata: Dict[str, Any] = Field(default_factory=dict)
    fetched_at: datetime = Field(default_factory=datetime.now)


class SyncResult(BaseModel):
    """同步结果"""

    source_type: SourceType
    success: bool
    total_fetched: int = 0
    total_processed: int = 0
    total_errors: int = 0
    errors: List[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime
    duration_seconds: float

    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
        self.total_errors += 1
