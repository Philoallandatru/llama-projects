"""MinerU PDF 解析器

使用 MinerU 进行高质量 PDF 解析，支持：
- 智能文档结构识别
- 自动目录检测和过滤
- 表格和公式提取
- Markdown 格式输出
- OCR 支持

安装: pip install mineru

MinerU 官网: https://mineru.net/
GitHub: https://github.com/opendatalab/MinerU
"""

import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

from llama_index.core import Document
from llama_index.core.readers.base import BaseReader

logger = logging.getLogger(__name__)

# 检查 MinerU 是否可用
try:
    import mineru
    MINERU_AVAILABLE = True
except ImportError:
    MINERU_AVAILABLE = False
    logger.warning(
        "MinerU not installed. Install with: pip install mineru\n"
        "Falling back to PyMuPDF reader."
    )


class MinerUReader(BaseReader):
    """MinerU PDF 阅读器

    使用 MinerU 进行智能 PDF 解析，特别适合：
    - 学术论文
    - 技术规格文档
    - 复杂布局的文档

    Args:
        skip_toc: 是否自动跳过目录页（默认 True）
        min_page_length: 最小页面长度，短于此长度的页面会被跳过（默认 50）
        method: 解析方法 "auto", "txt", "ocr"（默认 "auto"）
        backend: 后端类型（默认 "pipeline"）
        lang: 语言（默认 "ch"）
        formula_enable: 是否提取公式（默认 True）
        table_enable: 是否提取表格（默认 True）
    """

    def __init__(
        self,
        skip_toc: bool = True,
        min_page_length: int = 50,
        method: str = "auto",
        backend: str = "pipeline",
        lang: str = "ch",
        formula_enable: bool = True,
        table_enable: bool = True,
    ):
        if not MINERU_AVAILABLE:
            raise ImportError(
                "MinerU is not installed. Install with: pip install mineru"
            )

        self.skip_toc = skip_toc
        self.min_page_length = min_page_length
        self.method = method
        self.backend = backend
        self.lang = lang
        self.formula_enable = formula_enable
        self.table_enable = table_enable

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """加载 PDF 文件

        Args:
            file: PDF 文件路径
            extra_info: 额外的元数据

        Returns:
            Document 列表
        """
        file_path = Path(file)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.suffix.lower() == ".pdf":
            raise ValueError(f"File must be a PDF: {file_path}")

        logger.info(f"Parsing {file_path.name} with MinerU...")

        try:
            # 使用 MinerU CLI 解析（最稳定的方式）
            documents = self._parse_with_cli(file_path, extra_info)

            logger.info(f"Loaded {len(documents)} pages from {file_path.name}")
            return documents

        except Exception as e:
            logger.error(f"Failed to parse PDF with MinerU: {e}")
            raise

    def _parse_with_cli(
        self,
        file_path: Path,
        extra_info: Optional[Dict[str, Any]],
    ) -> List[Document]:
        """使用 MinerU CLI 解析 PDF

        Args:
            file_path: PDF 文件路径
            extra_info: 额外的元数据

        Returns:
            Document 列表
        """
        # 创建临时输出目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output = Path(temp_dir)

            # 构建 MinerU 命令
            cmd = [
                "mineru",
                "-p", str(file_path),
                "-o", str(temp_output),
                "-m", self.method,
                "-b", self.backend,
                "-l", self.lang,
            ]

            # 添加可选参数
            if not self.formula_enable:
                cmd.extend(["-f", "False"])
            if not self.table_enable:
                cmd.extend(["-t", "False"])

            # 执行命令
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
            )

            if result.returncode != 0:
                logger.error(f"MinerU failed: {result.stderr}")
                raise RuntimeError(f"MinerU parsing failed: {result.stderr}")

            # 查找输出的 Markdown 文件
            # MinerU 输出格式: output_dir/filename/filename.md
            pdf_name = file_path.stem
            md_file = temp_output / pdf_name / f"{pdf_name}.md"

            if not md_file.exists():
                # 尝试其他可能的位置
                md_files = list(temp_output.rglob("*.md"))
                if md_files:
                    md_file = md_files[0]
                else:
                    raise FileNotFoundError(f"MinerU output not found in {temp_output}")

            # 读取 Markdown 内容
            with open(md_file, "r", encoding="utf-8") as f:
                md_content = f.read()

            # 解析 Markdown 为 Documents
            documents = self._parse_markdown(md_content, file_path, extra_info)

            return documents

    def _parse_markdown(
        self,
        md_content: str,
        file_path: Path,
        extra_info: Optional[Dict[str, Any]],
    ) -> List[Document]:
        """解析 Markdown 内容为 Documents

        Args:
            md_content: Markdown 内容
            file_path: 原始 PDF 文件路径
            extra_info: 额外的元数据

        Returns:
            Document 列表
        """
        documents = []

        # 按页面分割
        pages = self._split_markdown_pages(md_content)

        for page_num, page_content in enumerate(pages, start=1):
            page_content = page_content.strip()

            # 过滤目录页
            if self.skip_toc and self._is_toc_content(page_content):
                logger.debug(f"Skipping TOC page: {page_num}")
                continue

            # 过滤短页面
            if len(page_content) < self.min_page_length:
                logger.debug(f"Skipping short page: {page_num} (length: {len(page_content)})")
                continue

            # 创建元数据
            metadata = {
                "page": page_num,
                "source": str(file_path),
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "format": "markdown",
                "parser": "mineru",
            }
            if extra_info:
                metadata.update(extra_info)

            documents.append(Document(text=page_content, metadata=metadata))

        return documents

    def _split_markdown_pages(self, md_content: str) -> List[str]:
        """分割 Markdown 内容为页面"""
        # 尝试按页面标记分割
        separators = [
            r'\n---\s*Page\s+\d+\s*---\n',
            r'\n##\s*Page\s+\d+\n',
            r'\n<!-- Page \d+ -->\n',
        ]

        for separator in separators:
            parts = re.split(separator, md_content)
            if len(parts) > 1:
                return [p for p in parts if p.strip()]

        # 按一级标题分割
        sections = re.split(r'\n#\s+', md_content)
        if len(sections) > 1:
            return [f"# {s}" if i > 0 else s for i, s in enumerate(sections) if s.strip()]

        # 按段落分组
        paragraphs = [p.strip() for p in md_content.split('\n\n') if p.strip()]
        if len(paragraphs) > 10:
            pages = []
            for i in range(0, len(paragraphs), 10):
                page = '\n\n'.join(paragraphs[i:i+10])
                pages.append(page)
            return pages

        # 整个文档作为一页
        return [md_content]

    def _is_toc_content(self, content: str) -> bool:
        """判断是否是目录"""
        content_lower = content.lower()

        # 目录标题
        toc_headers = ['# contents', '# 目录', '# table of contents', '# index']
        if any(header in content_lower for header in toc_headers):
            return True

        # 目录特征
        has_many_links = content.count('[') > 10
        has_dots = len(re.findall(r'\.{3,}', content)) > 5
        has_page_numbers = len(re.findall(r'\b\d{1,3}\b', content)) > 10
        has_chapter_numbers = len(re.findall(r'^\d+\.\d+', content, re.MULTILINE)) > 5

        features_count = sum([
            has_many_links,
            has_dots,
            has_page_numbers and (has_dots or has_chapter_numbers),
        ])

        return features_count >= 2


# 如果 MinerU 不可用，提供占位符
if not MINERU_AVAILABLE:
    class MinerUReader(BaseReader):
        def __init__(self, *args, **kwargs):
            raise ImportError("MinerU is not installed. Install with: pip install mineru")

        def load_data(self, *args, **kwargs):
            raise ImportError("MinerU is not installed. Install with: pip install mineru")
