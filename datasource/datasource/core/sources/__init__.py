"""Data source implementations"""

from .base import BaseDataSource
from .local import LocalDataSource
from .jira import JiraDataSource
from .confluence import ConfluenceDataSource

# PDF 阅读器
from .pdf_reader import get_pdf_reader, check_pdf_parsers, print_parser_status
from .enhanced_pdf_reader import EnhancedPDFReader

# MinerU 阅读器（如果可用）
try:
    from .mineru_reader import MinerUReader
    MINERU_AVAILABLE = True
except ImportError:
    MINERU_AVAILABLE = False
    MinerUReader = None

__all__ = [
    "BaseDataSource",
    "LocalDataSource",
    "JiraDataSource",
    "ConfluenceDataSource",
    # PDF 阅读器
    "get_pdf_reader",
    "check_pdf_parsers",
    "print_parser_status",
    "EnhancedPDFReader",
    "MinerUReader",
    "MINERU_AVAILABLE",
]
