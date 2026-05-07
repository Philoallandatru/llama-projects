"""本地文件数据源

本模块实现本地文件系统的数据源，支持扫描目录并解析各种文档格式。
"""

import json
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any, Optional
from datetime import datetime

from llama_index.core import Document
from llama_index.core import SimpleDirectoryReader

from .base import BaseDataSource
from ..models import SourceConfig
from .mineru_reader import MinerUReader

import logging
logger = logging.getLogger(__name__)


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

        # 初始化 MinerU PDF 阅读器（如果可用）
        try:
            self.mineru_reader = MinerUReader(
                skip_toc=True,
                min_page_length=50,
                method="auto",
                backend="pipeline",
                lang="ch",
                formula_enable=True,
                table_enable=True
            )
        except Exception as e:
            logger.warning(f"Failed to initialize MinerU reader: {e}")
            self.mineru_reader = None

    def fetch_raw(
        self,
        output_dir: Path,
        since: Optional[str] = None
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """扫描目录并保存文件元数据

        实现逻辑：
        1. 递归扫描目录
        2. 过滤支持的文件类型
        3. 如果提供 since，只返回修改时间晚于 since 的文件
        4. 提取文件元数据
        5. 保存为 JSON

        Args:
            output_dir: 原始数据保存目录
            since: 增量同步起始时间（ISO 8601 格式）

        Yields:
            (item_id, raw_data) 元组
            - item_id: 相对路径（用 / 分隔，去掉扩展名）
            - raw_data: 文件元数据
        """
        from datetime import datetime

        output_dir.mkdir(parents=True, exist_ok=True)

        # 解析 since 时间戳
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid since timestamp: {since}, performing full sync")

        # 递归扫描目录
        for file_path in self.root_path.rglob('*'):
            # 跳过目录和不支持的文件
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            # 增量同步：检查文件修改时间
            if since_dt:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < since_dt:
                    continue  # 跳过未修改的文件

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
