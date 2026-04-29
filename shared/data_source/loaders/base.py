"""
数据加载器基类

负责将原始文档转换为统一文档模型
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..schemas.models import RawDocument, UnifiedDocument, SourceType, DocumentStatus


class BaseLoader(ABC):
    """数据加载器基类"""

    def __init__(self, source_type: SourceType):
        """
        初始化加载器

        Args:
            source_type: 数据源类型
        """
        self.source_type = source_type

    @abstractmethod
    async def load(self, raw_doc: RawDocument) -> Optional[UnifiedDocument]:
        """
        加载原始文档并转换为统一文档

        Args:
            raw_doc: 原始文档

        Returns:
            Optional[UnifiedDocument]: 统一文档，如果加载失败返回 None
        """
        pass

    async def load_batch(self, raw_docs: List[RawDocument]) -> List[UnifiedDocument]:
        """
        批量加载文档

        Args:
            raw_docs: 原始文档列表

        Returns:
            List[UnifiedDocument]: 统一文档列表
        """
        results = []
        for raw_doc in raw_docs:
            try:
                doc = await self.load(raw_doc)
                if doc:
                    results.append(doc)
            except Exception as e:
                print(f"加载文档失败 {raw_doc.source_id}: {e}")
        return results

    def _create_base_document(
        self,
        raw_doc: RawDocument,
        content: str,
        title: Optional[str] = None,
        **kwargs
    ) -> UnifiedDocument:
        """
        创建基础统一文档

        Args:
            raw_doc: 原始文档
            content: 文本内容
            title: 标题
            **kwargs: 其他字段

        Returns:
            UnifiedDocument: 统一文档
        """
        return UnifiedDocument(
            id=f"{raw_doc.source_type.value}-{raw_doc.source_id}",
            content=content,
            title=title,
            source_type=raw_doc.source_type,
            source_id=raw_doc.source_id,
            metadata=raw_doc.metadata,
            status=DocumentStatus.PROCESSED,
            processed_at=datetime.now(),
            **kwargs
        )


class TextLoader(BaseLoader):
    """文本文件加载器"""

    def __init__(self):
        super().__init__(SourceType.TEXT)

    async def load(self, raw_doc: RawDocument) -> Optional[UnifiedDocument]:
        """加载文本文件"""
        try:
            content = raw_doc.raw_data
            if isinstance(content, bytes):
                content = content.decode('utf-8')

            return self._create_base_document(
                raw_doc=raw_doc,
                content=content,
                title=raw_doc.metadata.get('filename')
            )
        except Exception as e:
            print(f"加载文本文件失败: {e}")
            return None


class MarkdownLoader(BaseLoader):
    """Markdown 文件加载器"""

    def __init__(self):
        super().__init__(SourceType.MARKDOWN)

    async def load(self, raw_doc: RawDocument) -> Optional[UnifiedDocument]:
        """加载 Markdown 文件"""
        try:
            content = raw_doc.raw_data
            if isinstance(content, bytes):
                content = content.decode('utf-8')

            # 提取标题（第一个 # 标题）
            title = None
            lines = content.split('\n')
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break

            return self._create_base_document(
                raw_doc=raw_doc,
                content=content,
                title=title or raw_doc.metadata.get('filename')
            )
        except Exception as e:
            print(f"加载 Markdown 文件失败: {e}")
            return None
