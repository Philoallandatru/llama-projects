"""
LlamaIndex Reader 管理器

统一管理和配置 LlamaIndex Readers
"""
from typing import Dict, List, Optional, Any
from pathlib import Path

from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.readers.base import BaseReader


class ReaderManager:
    """LlamaIndex Reader 管理器"""

    def __init__(self):
        self.readers: Dict[str, BaseReader] = {}
        self._setup_default_readers()

    def _setup_default_readers(self):
        """设置默认的文件 Readers"""
        try:
            from llama_index.readers.file import (
                PDFReader,
                DocxReader,
                PptxReader,
            )

            self.file_extractors = {
                ".pdf": PDFReader(),
                ".docx": DocxReader(),
                ".doc": DocxReader(),
                ".pptx": PptxReader(),
                ".ppt": PptxReader(),
            }
        except ImportError:
            print("提示: 安装 llama-index-readers-file 以支持更多文件格式")
            print("  pip install llama-index-readers-file")
            self.file_extractors = {}

    def register_reader(self, name: str, reader: BaseReader):
        """
        注册自定义 Reader

        Args:
            name: Reader 名称
            reader: Reader 实例
        """
        self.readers[name] = reader
        print(f"已注册 Reader: {name}")

    def load_from_directory(
        self,
        directory: str,
        recursive: bool = True,
        required_exts: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        从目录加载文档

        Args:
            directory: 目录路径
            recursive: 是否递归
            required_exts: 需要的文件扩展名
            exclude: 排除的文件/目录

        Returns:
            List[Document]: LlamaIndex 文档列表
        """
        reader = SimpleDirectoryReader(
            input_dir=directory,
            recursive=recursive,
            required_exts=required_exts,
            exclude=exclude,
            file_extractor=self.file_extractors,
        )

        documents = reader.load_data()
        print(f"从 {directory} 加载了 {len(documents)} 个文档")
        return documents

    def load_from_files(self, file_paths: List[str]) -> List[Document]:
        """
        从文件列表加载文档

        Args:
            file_paths: 文件路径列表

        Returns:
            List[Document]: LlamaIndex 文档列表
        """
        reader = SimpleDirectoryReader(
            input_files=file_paths,
            file_extractor=self.file_extractors,
        )

        documents = reader.load_data()
        print(f"加载了 {len(documents)} 个文档")
        return documents

    def load_with_reader(
        self,
        reader_name: str,
        **kwargs
    ) -> List[Document]:
        """
        使用指定的 Reader 加载文档

        Args:
            reader_name: Reader 名称
            **kwargs: Reader 参数

        Returns:
            List[Document]: LlamaIndex 文档列表
        """
        reader = self.readers.get(reader_name)
        if not reader:
            raise ValueError(f"Reader {reader_name} 未注册")

        documents = reader.load_data(**kwargs)
        print(f"使用 {reader_name} 加载了 {len(documents)} 个文档")
        return documents

    def setup_jira_reader(
        self,
        email: str,
        api_token: str,
        server_url: str
    ):
        """
        设置 Jira Reader

        Args:
            email: Jira 邮箱
            api_token: API Token
            server_url: Jira 服务器 URL
        """
        try:
            from llama_index.readers.jira import JiraReader

            reader = JiraReader(
                email=email,
                api_token=api_token,
                server_url=server_url
            )
            self.register_reader("jira", reader)
        except ImportError:
            print("提示: 安装 llama-index-readers-jira")
            print("  pip install llama-index-readers-jira")

    def setup_confluence_reader(
        self,
        base_url: str,
        oauth2: Optional[Dict[str, str]] = None,
        api_token: Optional[str] = None,
    ):
        """
        设置 Confluence Reader

        Args:
            base_url: Confluence URL
            oauth2: OAuth2 配置
            api_token: API Token
        """
        try:
            from llama_index.readers.confluence import ConfluenceReader

            reader = ConfluenceReader(
                base_url=base_url,
                oauth2=oauth2,
                api_token=api_token
            )
            self.register_reader("confluence", reader)
        except ImportError:
            print("提示: 安装 llama-index-readers-confluence")
            print("  pip install llama-index-readers-confluence")

    def setup_notion_reader(self, integration_token: str):
        """
        设置 Notion Reader

        Args:
            integration_token: Notion Integration Token
        """
        try:
            from llama_index.readers.notion import NotionPageReader

            reader = NotionPageReader(integration_token=integration_token)
            self.register_reader("notion", reader)
        except ImportError:
            print("提示: 安装 llama-index-readers-notion")
            print("  pip install llama-index-readers-notion")

    def setup_google_drive_reader(self, credentials_path: Optional[str] = None):
        """
        设置 Google Drive Reader

        Args:
            credentials_path: Google 凭证文件路径
        """
        try:
            from llama_index.readers.google import GoogleDriveReader

            reader = GoogleDriveReader(credentials_path=credentials_path)
            self.register_reader("google_drive", reader)
        except ImportError:
            print("提示: 安装 llama-index-readers-google")
            print("  pip install llama-index-readers-google")
