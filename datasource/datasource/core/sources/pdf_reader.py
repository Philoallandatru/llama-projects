"""PDF 阅读器工厂

提供统一的 PDF 阅读器接口，根据可用性自动选择最佳解析器：
1. MinerU (magic-pdf) - 最智能，支持复杂布局和目录过滤
2. PyMuPDF (fitz) - 高质量，支持表格提取
3. pypdf - 基础解析器

使用示例:
    from datasource.core.sources.pdf_reader import get_pdf_reader

    # 自动选择最佳解析器
    reader = get_pdf_reader()
    documents = reader.load_data("document.pdf")

    # 指定解析器
    reader = get_pdf_reader(parser="mineru", skip_toc=True)
    documents = reader.load_data("document.pdf")
"""

import logging
from typing import Optional, Literal

from llama_index.core.readers.base import BaseReader

logger = logging.getLogger(__name__)

ParserType = Literal["mineru", "pymupdf", "pypdf", "auto"]


def get_pdf_reader(
    parser: ParserType = "auto",
    skip_toc: bool = True,
    **kwargs
) -> BaseReader:
    """获取 PDF 阅读器

    Args:
        parser: 解析器类型
            - "auto": 自动选择最佳可用解析器（默认）
            - "mineru": 使用 MinerU (magic-pdf)
            - "pymupdf": 使用 PyMuPDF (fitz)
            - "pypdf": 使用 pypdf
        skip_toc: 是否跳过目录页（仅 MinerU 支持）
        **kwargs: 传递给解析器的额外参数

    Returns:
        PDF 阅读器实例

    Raises:
        ImportError: 如果指定的解析器不可用
    """
    if parser == "auto":
        # 按优先级尝试
        try:
            return get_pdf_reader("mineru", skip_toc=skip_toc, **kwargs)
        except ImportError:
            logger.info("MinerU not available, trying PyMuPDF...")

        try:
            return get_pdf_reader("pymupdf", **kwargs)
        except ImportError:
            logger.info("PyMuPDF not available, trying pypdf...")

        try:
            return get_pdf_reader("pypdf", **kwargs)
        except ImportError:
            raise ImportError(
                "No PDF parser available. Install one of:\n"
                "  pip install magic-pdf  (recommended)\n"
                "  pip install pymupdf\n"
                "  pip install pypdf"
            )

    elif parser == "mineru":
        try:
            from .mineru_reader import MinerUReader
            logger.info("Using MinerU PDF reader")
            return MinerUReader(skip_toc=skip_toc, **kwargs)
        except ImportError as e:
            raise ImportError(
                "MinerU not installed. Install with: pip install magic-pdf"
            ) from e

    elif parser == "pymupdf":
        try:
            from .enhanced_pdf_reader import EnhancedPDFReader
            logger.info("Using PyMuPDF PDF reader")
            return EnhancedPDFReader(**kwargs)
        except ImportError as e:
            raise ImportError(
                "PyMuPDF not installed. Install with: pip install pymupdf"
            ) from e

    elif parser == "pypdf":
        try:
            from llama_index.readers.file import PDFReader
            logger.info("Using pypdf PDF reader")
            return PDFReader(**kwargs)
        except ImportError as e:
            raise ImportError(
                "pypdf not installed. Install with: pip install pypdf"
            ) from e

    else:
        raise ValueError(
            f"Unknown parser: {parser}. "
            f"Must be one of: 'auto', 'mineru', 'pymupdf', 'pypdf'"
        )


def check_pdf_parsers() -> dict:
    """检查可用的 PDF 解析器

    Returns:
        字典，包含每个解析器的可用性
    """
    parsers = {}

    # 检查 MinerU
    try:
        from magic_pdf.pipe.UNIPipe import UNIPipe
        parsers["mineru"] = True
    except ImportError:
        parsers["mineru"] = False

    # 检查 PyMuPDF
    try:
        import fitz
        parsers["pymupdf"] = True
    except ImportError:
        parsers["pymupdf"] = False

    # 检查 pypdf
    try:
        from pypdf import PdfReader
        parsers["pypdf"] = True
    except ImportError:
        parsers["pypdf"] = False

    return parsers


def print_parser_status():
    """打印 PDF 解析器状态"""
    parsers = check_pdf_parsers()

    print("PDF Parser Status:")
    print("-" * 50)

    for parser, available in parsers.items():
        status = "✓ Available" if available else "✗ Not installed"
        print(f"  {parser:12s}: {status}")

        if not available:
            if parser == "mineru":
                print(f"               Install: pip install magic-pdf")
            elif parser == "pymupdf":
                print(f"               Install: pip install pymupdf")
            elif parser == "pypdf":
                print(f"               Install: pip install pypdf")

    print("-" * 50)

    # 推荐
    if parsers["mineru"]:
        print("Recommended: MinerU (best quality, TOC filtering)")
    elif parsers["pymupdf"]:
        print("Recommended: PyMuPDF (good quality, table extraction)")
    elif parsers["pypdf"]:
        print("Recommended: pypdf (basic parsing)")
    else:
        print("Warning: No PDF parser installed!")


if __name__ == "__main__":
    # 测试
    print_parser_status()
