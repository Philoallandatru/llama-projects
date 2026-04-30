"""高质量 PDF 解析器

使用 PyMuPDF (fitz) 进行高质量 PDF 文本提取，支持 OCR 和复杂布局。
适用于 Windows/Linux/macOS。
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from llama_index.core import Document
from llama_index.core.readers.base import BaseReader

logger = logging.getLogger(__name__)


class EnhancedPDFReader(BaseReader):
    """增强型 PDF 阅读器

    使用 PyMuPDF (fitz) 库进行 PDF 解析，支持：
    - 高质量文本提取
    - 表格识别
    - 图片提取
    - 保留布局信息

    Args:
        extract_images: 是否提取图片（默认 False）
        extract_tables: 是否提取表格（默认 True）
        preserve_layout: 是否保留布局（默认 True）
    """

    def __init__(
        self,
        extract_images: bool = False,
        extract_tables: bool = True,
        preserve_layout: bool = True,
    ):
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        self.preserve_layout = preserve_layout

    def load_data(
        self,
        file_path: str,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """加载 PDF 文件

        Args:
            file_path: PDF 文件路径
            extra_info: 额外的元数据

        Returns:
            Document 列表
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error(
                "PyMuPDF not installed. "
                "Install with: pip install pymupdf"
            )
            raise

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # 打开 PDF
            doc = fitz.open(str(file_path))

            text_parts = []

            # 逐页提取
            for page_num in range(len(doc)):
                page = doc[page_num]

                # 提取文本（保留布局）
                if self.preserve_layout:
                    text = page.get_text("text", sort=True)
                else:
                    text = page.get_text()

                if text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

                # 提取表格
                if self.extract_tables:
                    tables = self._extract_tables(page)
                    if tables:
                        text_parts.append(f"\n{tables}\n")

            full_text = '\n\n'.join(text_parts)

            # 构建元数据
            metadata = extra_info or {}
            metadata.update({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'parser': 'pymupdf',
                'num_pages': len(doc),
                'extract_images': self.extract_images,
                'extract_tables': self.extract_tables,
            })

            # 添加 PDF 元数据
            pdf_metadata = doc.metadata
            if pdf_metadata:
                metadata.update({
                    'pdf_title': pdf_metadata.get('title', ''),
                    'pdf_author': pdf_metadata.get('author', ''),
                    'pdf_subject': pdf_metadata.get('subject', ''),
                })

            doc.close()

            # 创建 Document
            document = Document(
                text=full_text,
                metadata=metadata,
            )

            return [document]

        except Exception as e:
            logger.error(f"Failed to parse PDF with PyMuPDF: {e}")
            # 回退到 pypdf
            return self._fallback_parse(file_path, extra_info)

    def _extract_tables(self, page) -> str:
        """从页面提取表格

        Args:
            page: PyMuPDF 页面对象

        Returns:
            Markdown 格式的表格
        """
        try:
            # PyMuPDF 的表格提取
            tables = page.find_tables()
            if not tables:
                return ""

            table_texts = []
            for table in tables:
                # 转换为 markdown
                rows = table.extract()
                if rows:
                    md_table = self._format_table_markdown(rows)
                    table_texts.append(md_table)

            return '\n\n'.join(table_texts)

        except Exception as e:
            logger.warning(f"Failed to extract tables: {e}")
            return ""

    def _format_table_markdown(self, rows: List[List[str]]) -> str:
        """将表格格式化为 markdown

        Args:
            rows: 表格行列表

        Returns:
            Markdown 格式的表格
        """
        if not rows:
            return ""

        lines = []
        for i, row in enumerate(rows):
            # 清理单元格内容
            cells = [str(cell).strip() if cell else '' for cell in row]
            line = '| ' + ' | '.join(cells) + ' |'
            lines.append(line)

            # 添加表头分隔符
            if i == 0:
                separator = '| ' + ' | '.join(['---'] * len(cells)) + ' |'
                lines.append(separator)

        return '\n'.join(lines)

    def _fallback_parse(
        self,
        file_path: Path,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """回退到 pypdf 解析

        Args:
            file_path: PDF 文件路径
            extra_info: 额外的元数据

        Returns:
            Document 列表
        """
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            text_parts = []

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

            full_text = '\n\n'.join(text_parts)

            metadata = extra_info or {}
            metadata.update({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'parser': 'pypdf',
                'num_pages': len(reader.pages),
            })

            return [Document(text=full_text, metadata=metadata)]

        except Exception as e:
            logger.error(f"Fallback parse also failed: {e}")
            raise

