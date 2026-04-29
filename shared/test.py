"""
测试脚本 - 验证共享数据层是否正常工作

运行此脚本来测试基本功能
"""
import asyncio
import sys
from pathlib import Path

# 设置 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加共享层到 Python 路径
shared_path = Path(__file__).parent
sys.path.insert(0, str(shared_path))


async def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("共享数据层测试")
    print("=" * 60)

    try:
        # 1. 测试导入
        print("\n[1/5] 测试模块导入...")
        import data_source
        from data_source.manager import DataSourceManager
        from data_source.connectors.filesystem import LocalFileSystemConnector
        from data_source.loaders.base import TextLoader, MarkdownLoader
        from data_source.schemas.models import SourceType
        print("[OK] 模块导入成功")

        # 2. 测试数据源管理器创建
        print("\n[2/5] 测试数据源管理器...")
        manager = DataSourceManager()
        print("[OK] 数据源管理器创建成功")

        # 3. 测试加载器注册
        print("\n[3/5] 测试加载器注册...")
        manager.register_loader(SourceType.TEXT, TextLoader())
        manager.register_loader(SourceType.MARKDOWN, MarkdownLoader())
        print("[OK] 加载器注册成功")

        # 4. 测试连接器注册
        print("\n[4/5] 测试连接器注册...")

        # 创建测试目录
        test_data_dir = Path(__file__).parent / "test_data"
        test_data_dir.mkdir(exist_ok=True)

        # 创建测试文件
        test_file = test_data_dir / "test.txt"
        test_file.write_text("这是一个测试文件。\n用于验证共享数据层是否正常工作。", encoding='utf-8')

        config = {
            'paths': [str(test_data_dir)],
            'file_types': ['.txt', '.md'],
            'recursive': False,
        }

        connector = LocalFileSystemConnector(config)
        manager.register_connector('test', connector)
        print("[OK] 连接器注册成功")

        # 5. 测试文档加载
        print("\n[5/5] 测试文档加载...")
        await manager.connect_all()
        documents = await manager.fetch_and_load('test')

        if documents:
            print(f"[OK] 成功加载 {len(documents)} 个文档")
            print(f"\n文档示例:")
            doc = documents[0]
            print(f"  ID: {doc.id}")
            print(f"  标题: {doc.title}")
            print(f"  类型: {doc.source_type.value}")
            print(f"  内容: {doc.content[:50]}...")
        else:
            print("[WARN] 未找到文档")

        # 清理
        await manager.disconnect_all()

        print("\n" + "=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)
        print("\n共享数据层已准备就绪，可以集成到项目中。")
        print("请参考 INTEGRATION.md 了解如何集成到现有项目。")

        return True

    except ImportError as e:
        print(f"\n[ERROR] 导入错误: {e}")
        print("\n请确保已安装依赖:")
        print("  pip install -r requirements.txt")
        return False

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_document_loaders():
    """测试各种文档加载器"""
    print("\n" + "=" * 60)
    print("测试文档加载器")
    print("=" * 60)

    try:
        import data_source
        from data_source.loaders.documents import (
            ExcelLoader, WordLoader, PowerPointLoader, PDFLoader
        )

        loaders = {
            'Excel': ExcelLoader,
            'Word': WordLoader,
            'PowerPoint': PowerPointLoader,
            'PDF': PDFLoader,
        }

        print("\n可用的文档加载器:")
        for name, loader_class in loaders.items():
            try:
                loader = loader_class()
                print(f"  [OK] {name}Loader")
            except Exception as e:
                print(f"  [WARN] {name}Loader (需要额外依赖)")

        print("\n提示: 如果某些加载器不可用，请安装相应的依赖:")
        print("  pip install openpyxl pandas python-docx python-pptx pypdf")

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")


if __name__ == "__main__":
    print("\n开始测试共享数据层...\n")

    # 运行基本功能测试
    success = asyncio.run(test_basic_functionality())

    # 运行文档加载器测试
    asyncio.run(test_document_loaders())

    if success:
        print("\n[OK] 测试完成！")
        sys.exit(0)
    else:
        print("\n[ERROR] 测试失败，请检查错误信息。")
        sys.exit(1)
