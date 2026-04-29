"""
快速开始指南

演示如何快速集成共享数据层到现有项目
"""
import asyncio
from shared.data_source.manager import DataSourceManager
from shared.data_source.connectors.filesystem import LocalFileSystemConnector
from shared.data_source.loaders.base import TextLoader, MarkdownLoader
from shared.data_source.loaders.documents import (
    ExcelLoader, WordLoader, PowerPointLoader, PDFLoader
)
from shared.data_source.schemas.models import SourceType


async def quick_start():
    """快速开始示例"""

    # 1. 创建管理器
    manager = DataSourceManager()

    # 2. 注册所有加载器
    loaders = {
        SourceType.TEXT: TextLoader(),
        SourceType.MARKDOWN: MarkdownLoader(),
        SourceType.EXCEL: ExcelLoader(),
        SourceType.WORD: WordLoader(),
        SourceType.POWERPOINT: PowerPointLoader(),
        SourceType.PDF: PDFLoader(),
    }

    for source_type, loader in loaders.items():
        manager.register_loader(source_type, loader)

    # 3. 配置并注册文件系统连接器
    config = {
        'paths': ['./data'],  # 你的数据目录
        'file_types': ['.md', '.txt', '.pdf', '.docx', '.xlsx'],
        'recursive': True,
    }

    connector = LocalFileSystemConnector(config)
    manager.register_connector('docs', connector)

    # 4. 连接并加载文档
    await manager.connect_all()
    documents = await manager.fetch_and_load('docs')

    print(f"加载了 {len(documents)} 个文档")

    # 5. 使用文档（例如：创建索引）
    # 这里可以集成到你的 LlamaIndex 工作流中
    return documents


# 集成到现有项目的示例
async def integrate_with_existing_project():
    """集成到现有项目示例"""

    # 假设你有一个现有的 workflow.py
    from llama_index.core import VectorStoreIndex, Document
    from llama_index.core.settings import Settings

    # 使用共享数据层加载文档
    manager = DataSourceManager()

    # ... 注册加载器和连接器（同上）

    # 获取统一文档
    unified_docs = await quick_start()

    # 转换为 LlamaIndex Document
    llama_docs = [
        Document(
            text=doc.content,
            metadata={
                'title': doc.title,
                'source_type': doc.source_type.value,
                'source_id': doc.source_id,
                **doc.metadata
            }
        )
        for doc in unified_docs
    ]

    # 创建索引
    index = VectorStoreIndex.from_documents(
        llama_docs,
        embed_model=Settings.embed_model
    )

    return index


if __name__ == "__main__":
    # 运行快速开始
    asyncio.run(quick_start())
