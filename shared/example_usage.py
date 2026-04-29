"""
使用示例

演示如何使用共享数据层
"""
import asyncio
from pathlib import Path

from shared.data_source.manager import DataSourceManager
from shared.data_source.connectors.filesystem import LocalFileSystemConnector
from shared.data_source.loaders.base import TextLoader, MarkdownLoader
from shared.data_source.loaders.documents import (
    ExcelLoader,
    WordLoader,
    PowerPointLoader,
    PDFLoader,
    ImageLoader
)
from shared.data_source.schemas.models import SourceType


async def main():
    """主函数"""

    # 1. 创建数据源管理器
    manager = DataSourceManager()

    # 2. 注册加载器
    manager.register_loader(SourceType.TEXT, TextLoader())
    manager.register_loader(SourceType.MARKDOWN, MarkdownLoader())
    manager.register_loader(SourceType.EXCEL, ExcelLoader())
    manager.register_loader(SourceType.WORD, WordLoader())
    manager.register_loader(SourceType.POWERPOINT, PowerPointLoader())
    manager.register_loader(SourceType.PDF, PDFLoader())
    manager.register_loader(SourceType.IMAGE, ImageLoader())

    # 3. 注册文件系统连接器
    # 配置要扫描的路径和文件类型
    fs_config = {
        'paths': [
            './chat/data',
            './deep-serach/data',
            './data-explore/data',
        ],
        'file_types': [
            '.xlsx', '.xls',      # Excel
            '.docx', '.doc',      # Word
            '.pptx', '.ppt',      # PowerPoint
            '.md',                # Markdown
            '.pdf',               # PDF
            '.txt',               # Text
            '.png', '.jpg',       # Image
        ],
        'recursive': True,
        'watch': False,
    }

    fs_connector = LocalFileSystemConnector(fs_config)
    manager.register_connector('filesystem', fs_connector)

    # 4. 连接所有数据源
    print("\n=== 连接数据源 ===")
    connection_results = await manager.connect_all()

    if not all(connection_results.values()):
        print("部分数据源连接失败")
        return

    # 5. 同步数据（增量同步）
    print("\n=== 同步数据 ===")
    sync_results = await manager.sync_all(incremental=True, parallel=False)

    for result in sync_results:
        print(f"\n同步结果:")
        print(f"  数据源类型: {result.source_type.value}")
        print(f"  成功: {result.success}")
        print(f"  获取: {result.total_fetched} 条")
        print(f"  处理: {result.total_processed} 条")
        print(f"  错误: {result.total_errors} 条")
        print(f"  耗时: {result.duration_seconds:.2f} 秒")
        if result.errors:
            print(f"  错误详情: {result.errors[:3]}")  # 只显示前3个错误

    # 6. 获取并加载文档
    print("\n=== 获取并加载文档 ===")
    documents = await manager.fetch_and_load('filesystem')

    print(f"\n成功加载 {len(documents)} 个文档")

    # 7. 显示文档信息
    if documents:
        print("\n=== 文档示例 ===")
        for i, doc in enumerate(documents[:3], 1):  # 只显示前3个
            print(f"\n文档 {i}:")
            print(f"  ID: {doc.id}")
            print(f"  标题: {doc.title}")
            print(f"  类型: {doc.source_type.value}")
            print(f"  来源: {doc.source_id}")
            print(f"  状态: {doc.status.value}")
            print(f"  内容长度: {len(doc.content)} 字符")
            print(f"  内容预览: {doc.content[:100]}...")
            if doc.metadata:
                print(f"  元数据: {list(doc.metadata.keys())}")

    # 8. 按类型统计
    print("\n=== 文档类型统计 ===")
    type_counts = {}
    for doc in documents:
        type_counts[doc.source_type.value] = type_counts.get(doc.source_type.value, 0) + 1

    for doc_type, count in sorted(type_counts.items()):
        print(f"  {doc_type}: {count} 个")

    # 9. 断开连接
    print("\n=== 断开连接 ===")
    await manager.disconnect_all()

    print("\n完成！")


if __name__ == "__main__":
    asyncio.run(main())
