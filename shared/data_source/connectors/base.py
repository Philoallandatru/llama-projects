"""
数据源连接器基类

所有数据源连接器都需要实现这个接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..schemas.models import RawDocument, SyncResult, SourceType, UnifiedDocument


class BaseConnector(ABC):
    """数据源连接器基类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化连接器

        Args:
            config: 连接器配置
        """
        self.config = config
        self.source_type: SourceType = self._get_source_type()
        self._connected = False

    @abstractmethod
    def _get_source_type(self) -> SourceType:
        """返回数据源类型"""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """
        连接到数据源

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass

    @abstractmethod
    async def fetch(self, **kwargs) -> List[RawDocument]:
        """
        从数据源获取原始数据

        Args:
            **kwargs: 查询参数

        Returns:
            List[RawDocument]: 原始文档列表
        """
        pass

    @abstractmethod
    async def sync(self, incremental: bool = True) -> SyncResult:
        """
        同步数据

        Args:
            incremental: 是否增量同步

        Returns:
            SyncResult: 同步结果
        """
        pass

    async def test_connection(self) -> bool:
        """
        测试连接

        Returns:
            bool: 连接是否正常
        """
        try:
            return await self.connect()
        except Exception:
            return False

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected


class FileSystemConnector(BaseConnector):
    """文件系统连接器基类"""

    def _get_source_type(self) -> SourceType:
        # 子类需要根据文件类型返回具体的 SourceType
        return SourceType.TEXT

    @abstractmethod
    async def list_files(self, path: str, recursive: bool = True) -> List[str]:
        """
        列出文件

        Args:
            path: 文件路径
            recursive: 是否递归

        Returns:
            List[str]: 文件路径列表
        """
        pass

    @abstractmethod
    async def read_file(self, file_path: str) -> RawDocument:
        """
        读取文件

        Args:
            file_path: 文件路径

        Returns:
            RawDocument: 原始文档
        """
        pass


class APIConnector(BaseConnector):
    """API 连接器基类（用于 Jira、Confluence 等）"""

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        认证

        Returns:
            bool: 认证是否成功
        """
        pass

    @abstractmethod
    async def get_item(self, item_id: str) -> Optional[RawDocument]:
        """
        获取单个项目

        Args:
            item_id: 项目ID

        Returns:
            Optional[RawDocument]: 原始文档，如果不存在返回 None
        """
        pass

    @abstractmethod
    async def list_items(self, **filters) -> List[RawDocument]:
        """
        列出项目

        Args:
            **filters: 过滤条件

        Returns:
            List[RawDocument]: 原始文档列表
        """
        pass
