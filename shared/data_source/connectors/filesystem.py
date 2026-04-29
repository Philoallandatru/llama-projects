"""
文件系统连接器实现

支持多种文档格式：Excel, Word, PowerPoint, Markdown, PDF, Text, Image
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import mimetypes

from .base import FileSystemConnector
from ..schemas.models import RawDocument, SyncResult, SourceType


class LocalFileSystemConnector(FileSystemConnector):
    """本地文件系统连接器"""

    # 文件扩展名到数据源类型的映射
    EXTENSION_MAP = {
        '.xlsx': SourceType.EXCEL,
        '.xls': SourceType.EXCEL,
        '.docx': SourceType.WORD,
        '.doc': SourceType.WORD,
        '.pptx': SourceType.POWERPOINT,
        '.ppt': SourceType.POWERPOINT,
        '.md': SourceType.MARKDOWN,
        '.pdf': SourceType.PDF,
        '.txt': SourceType.TEXT,
        '.png': SourceType.IMAGE,
        '.jpg': SourceType.IMAGE,
        '.jpeg': SourceType.IMAGE,
    }

    def __init__(self, config: Dict[str, Any]):
        """
        初始化文件系统连接器

        Args:
            config: 配置，包含：
                - paths: List[str] 要扫描的路径列表
                - file_types: List[str] 要包含的文件类型（扩展名）
                - recursive: bool 是否递归扫描子目录
                - watch: bool 是否监控文件变化
        """
        super().__init__(config)
        self.paths = config.get('paths', [])
        self.file_types = config.get('file_types', list(self.EXTENSION_MAP.keys()))
        self.recursive = config.get('recursive', True)
        self.watch = config.get('watch', False)
        self._last_sync: Dict[str, datetime] = {}

    def _get_source_type(self) -> SourceType:
        return SourceType.TEXT  # 默认类型

    async def connect(self) -> bool:
        """连接（验证路径是否存在）"""
        try:
            for path in self.paths:
                if not os.path.exists(path):
                    print(f"路径不存在: {path}")
                    return False
            self._connected = True
            return True
        except Exception as e:
            print(f"连接文件系统失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        self._connected = False

    async def list_files(self, path: str, recursive: bool = True) -> List[str]:
        """
        列出文件

        Args:
            path: 文件路径
            recursive: 是否递归

        Returns:
            List[str]: 文件路径列表
        """
        files = []
        path_obj = Path(path)

        if not path_obj.exists():
            return files

        if path_obj.is_file():
            if self._is_supported_file(str(path_obj)):
                files.append(str(path_obj))
        elif path_obj.is_dir():
            if recursive:
                for file_path in path_obj.rglob('*'):
                    if file_path.is_file() and self._is_supported_file(str(file_path)):
                        files.append(str(file_path))
            else:
                for file_path in path_obj.glob('*'):
                    if file_path.is_file() and self._is_supported_file(str(file_path)):
                        files.append(str(file_path))

        return files

    def _is_supported_file(self, file_path: str) -> bool:
        """检查文件是否支持"""
        ext = Path(file_path).suffix.lower()
        return ext in self.file_types

    def _get_file_source_type(self, file_path: str) -> SourceType:
        """根据文件扩展名获取数据源类型"""
        ext = Path(file_path).suffix.lower()
        return self.EXTENSION_MAP.get(ext, SourceType.TEXT)

    async def read_file(self, file_path: str) -> RawDocument:
        """
        读取文件

        Args:
            file_path: 文件路径

        Returns:
            RawDocument: 原始文档
        """
        path_obj = Path(file_path)
        source_type = self._get_file_source_type(file_path)

        # 获取文件元数据
        stat = path_obj.stat()
        metadata = {
            'filename': path_obj.name,
            'filepath': str(path_obj.absolute()),
            'extension': path_obj.suffix,
            'size_bytes': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
            'mime_type': mimetypes.guess_type(file_path)[0],
        }

        # 读取文件内容
        # 对于文本类型，直接读取；对于二进制类型，读取为 bytes
        if source_type in [SourceType.TEXT, SourceType.MARKDOWN]:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = f.read()
        else:
            with open(file_path, 'rb') as f:
                raw_data = f.read()

        return RawDocument(
            source_type=source_type,
            source_id=str(path_obj.absolute()),
            raw_data=raw_data,
            metadata=metadata,
            fetched_at=datetime.now()
        )

    async def fetch(self, **kwargs) -> List[RawDocument]:
        """
        获取所有文件

        Args:
            **kwargs: 可选参数
                - paths: List[str] 覆盖配置的路径
                - file_types: List[str] 覆盖配置的文件类型

        Returns:
            List[RawDocument]: 原始文档列表
        """
        paths = kwargs.get('paths', self.paths)
        self.file_types = kwargs.get('file_types', self.file_types)

        all_files = []
        for path in paths:
            files = await self.list_files(path, self.recursive)
            all_files.extend(files)

        # 读取所有文件
        raw_docs = []
        for file_path in all_files:
            try:
                raw_doc = await self.read_file(file_path)
                raw_docs.append(raw_doc)
            except Exception as e:
                print(f"读取文件失败 {file_path}: {e}")

        return raw_docs

    async def sync(self, incremental: bool = True) -> SyncResult:
        """
        同步文件

        Args:
            incremental: 是否增量同步（只同步修改过的文件）

        Returns:
            SyncResult: 同步结果
        """
        started_at = datetime.now()
        result = SyncResult(
            source_type=SourceType.TEXT,  # 混合类型，使用默认
            success=False,
            started_at=started_at,
            completed_at=started_at,
            duration_seconds=0
        )

        try:
            # 获取所有文件
            all_files = []
            for path in self.paths:
                files = await self.list_files(path, self.recursive)
                all_files.extend(files)

            result.total_fetched = len(all_files)

            # 如果是增量同步，过滤未修改的文件
            if incremental:
                files_to_sync = []
                for file_path in all_files:
                    last_sync = self._last_sync.get(file_path)
                    modified_at = datetime.fromtimestamp(
                        Path(file_path).stat().st_mtime
                    )
                    if not last_sync or modified_at > last_sync:
                        files_to_sync.append(file_path)
            else:
                files_to_sync = all_files

            # 读取文件
            for file_path in files_to_sync:
                try:
                    await self.read_file(file_path)
                    self._last_sync[file_path] = datetime.now()
                    result.total_processed += 1
                except Exception as e:
                    result.add_error(f"读取文件失败 {file_path}: {e}")

            result.success = True

        except Exception as e:
            result.add_error(f"同步失败: {e}")

        finally:
            result.completed_at = datetime.now()
            result.duration_seconds = (
                result.completed_at - result.started_at
            ).total_seconds()

        return result
