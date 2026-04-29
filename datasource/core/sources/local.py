"""本地文件数据源

本模块实现本地文件系统的数据源，支持扫描目录并解析各种文档格式。
"""

import json
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any
from datetime import datetime

from llama_index.core import Document
from llama_index.core import SimpleDirectoryReader

from .base import BaseDataSource
from ..models import SourceConfig


class LocalDataSource(BaseDataSource):
    """本地文件数据源

    支持的文件类型：
    - PDF (.pdf)
    - Word (.docx, .doc)
    - Markdown (.md)
    - Text (.txt)
    - Excel (.xlsx, .xls)
    - PowerPoint (.pptx, .ppt)

    特点：
    1. 递归扫描目录
    2. 自动识别文件类型
    3. 提取文件元数据（修改时间、大小等）
    4. 使用 LlamaIndex 的 SimpleDirectoryReader 进行解析
    """

    # 支持的文件扩展名
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.md', '.txt',
        '.xlsx', '.xls', '.pptx', '.ppt'
    }

    def __init__(self, config: SourceConfig):
        """初始化本地文件数据源

        Args:
            config: 数据源配置，必须包含 path 字段

        Raises:
            ValueError: 如果 path 不存在或不是目录
        """
        super().__init__(config)

        # 验证路径
        self.root_path = Path(config.path)
        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {config.path}")
        if not self.root_path.is_dir():
            raise ValueError(f"Path is not a directory: {config.path}")

    def fetch_raw(
        self,
        output_dir: Path
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """扫描目录并保存文件元数据

        实现逻辑：
        1. 递归扫描目录
        2. 过滤支持的文件类型
        3. 提取文件元数据
        4. 保存为 JSON

        Args:
            output_dir: 原始数据保存目录

        Yields:
            (item_id, raw_data) 元组
            - item_id: 相对路径（用 / 分隔，去掉扩展名）
            - raw_data: 文件元数据
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # 递归扫描目录
        for file_path in self.root_path.rglob('*'):
            # 跳过目录和不支持的文件
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            # 计算相对路径作为 item_id
            rel_path = file_path.relative_to(self.root_path)
            # 使用 / 分隔符，去掉扩展名
            item_id = str(rel_path.with_suffix('')).replace('\\', '/')

            # 提取文件元数据
            stat = file_path.stat()
            raw_data = {
                'item_id': item_id,
                'file_path': str(file_path),
                'relative_path': str(rel_path),
                'file_name': file_path.name,
                'file_size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'extension': file_path.suffix.lower(),
            }

            # 保存为 JSON
            output_file = output_dir / f"{self._sanitize_filename(item_id)}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False)

            yield item_id, raw_data

    def build_document(
        self,
        item_id: str,
        raw_data: Dict[str, Any],
        assets_dir: Path
    ) -> Document:
        """将文件转换为 LlamaIndex Document

        实现逻辑：
        1. 使用 SimpleDirectoryReader 解析文件
        2. 提取文本内容
        3. 构建 metadata
        4. 返回 Document

        Args:
            item_id: 文件标识（相对路径，无扩展名）
            raw_data: 文件元数据
            assets_dir: 附件保存目录（本地文件不需要）

        Returns:
            LlamaIndex Document 实例

        Raises:
            ValueError: 如果文件不存在或解析失败
        """
        file_path = Path(raw_data['file_path'])

        # 验证文件存在
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        try:
            # 使用 SimpleDirectoryReader 解析单个文件
            reader = SimpleDirectoryReader(
                input_files=[str(file_path)]
            )
            documents = reader.load_data()

            if not documents:
                raise ValueError(f"Failed to parse file: {file_path}")

            # 获取第一个文档（单文件只有一个）
            doc = documents[0]

            # 增强 metadata
            doc.metadata.update({
                'source_name': self.config.name,
                'source_type': self.config.type.value,
                'item_id': item_id,
                'file_name': raw_data['file_name'],
                'file_path': raw_data['relative_path'],
                'file_size': raw_data['file_size'],
                'modified_time': raw_data['modified_time'],
                'created_time': raw_data['created_time'],
                'extension': raw_data['extension'],
            })

            # 如果文本为空，使用文件名作为标题
            if not doc.text or doc.text.strip() == '':
                doc.text = f"# {raw_data['file_name']}\n\n(Empty file)"

            return doc

        except Exception as e:
            raise ValueError(f"Failed to build document for {file_path}: {e}")
