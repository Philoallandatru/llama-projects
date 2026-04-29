"""
使用 LlamaIndex Readers 的完整示例
"""
import asyncio
from pathlib import Path

from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.settings import Settings as LlamaSettings

# 导入共享层
from readers.manager import ReaderManager
from governance.quality import DataQualityChecker
from governance.security import PIIFilter


async def example_basic():
    """基础示例：从目录加载文档"""
    print("=" * 60)
    print("示例 1: 基础文档加载")
    print("=" * 60)

    # 创建 Reader 管理器
    manager = ReaderManager()

    # 从目录加载文档
    documents = manager.load_from_directory(
        directory="../chat/data",
        recursive=True,
        required_exts=[".md", ".txt", ".pdf", ".docx"]
    )

    print(f"\n加载了 {len(documents)} 个文档")
    if documents:
        print(f"示例文档: {documents[0].metadata.get('file_name', 'unknown')}")

    return documents


async def example_with_governance():
    """示例：使用数据治理"""
    print("\n" + "=" * 60)
    print("示例 2: 数据治理（质量检查 + PII 过滤）")
    print("=" * 60)

    # 1. 加载文档
    manager = ReaderManager()
    documents = manager.load_from_directory("../chat/data")

    print(f"\n原始文档数: {len(documents)}")

    # 2. 质量检查
    quality_checker = DataQualityChecker({
        "min_content_length": 50,
        "remove_duplicates": True
    })

    validated_docs, metrics = quality_checker.validate(documents)
    print(f"\n质量检查:")
    print(f"  通过: {metrics.passed_docs}/{metrics.total_docs}")
    print(f"  通过率: {metrics.get_summary()['pass_rate']:.1%}")

    # 3. PII 过滤
    pii_filter = PIIFilter({
        "enabled_filters": ["email", "phone", "id_card"],
        "redact_mode": "mask"
    })

    # 先扫描
    scan_report = pii_filter.scan(validated_docs)
    print(f"\nPII 扫描:")
    print(f"  包含 PII 的文档: {scan_report['docs_with_pii']}/{scan_report['total_docs']}")
    if scan_report['pii_types']:
        print(f"  发现的 PII 类型: {list(scan_report['pii_types'].keys())}")

    # 过滤
    safe_docs = pii_filter.filter(validated_docs)

    # 4. 丰富元数据
    enriched_docs = quality_checker.enrich_metadata(safe_docs)

    print(f"\n最终文档数: {len(enriched_docs)}")

    return enriched_docs


async def example_create_index():
    """示例：创建索引"""
    print("\n" + "=" * 60)
    print("示例 3: 创建 LlamaIndex 索引")
    print("=" * 60)

    # 1. 加载并治理文档
    manager = ReaderManager()
    documents = manager.load_from_directory("../chat/data")

    quality_checker = DataQualityChecker()
    validated_docs, _ = quality_checker.validate(documents)

    pii_filter = PIIFilter()
    safe_docs = pii_filter.filter(validated_docs)

    # 2. 创建索引
    print(f"\n使用 {len(safe_docs)} 个文档创建索引...")
    index = VectorStoreIndex.from_documents(
        safe_docs,
        embed_model=Settings.embed_model
    )

    print("索引创建完成！")

    # 3. 测试查询
    query_engine = index.as_query_engine()
    response = query_engine.query("这些文档的主要内容是什么？")
    print(f"\n测试查询结果: {response}")

    return index


async def example_jira_confluence():
    """示例：连接 Jira 和 Confluence"""
    print("\n" + "=" * 60)
    print("示例 4: Jira & Confluence 集成")
    print("=" * 60)

    manager = ReaderManager()

    # 设置 Jira Reader
    # manager.setup_jira_reader(
    #     email="your-email@example.com",
    #     api_token="your-api-token",
    #     server_url="https://your-domain.atlassian.net"
    # )

    # 设置 Confluence Reader
    # manager.setup_confluence_reader(
    #     base_url="https://your-domain.atlassian.net/wiki",
    #     api_token="your-api-token"
    # )

    print("提示: 取消注释上面的代码并填入你的凭证")
    print("然后使用:")
    print("  jira_docs = manager.load_with_reader('jira', query='project=PROJ')")
    print("  confluence_docs = manager.load_with_reader('confluence', space_key='SPACE')")


async def example_multi_source():
    """示例：多数据源集成"""
    print("\n" + "=" * 60)
    print("示例 5: 多数据源集成")
    print("=" * 60)

    manager = ReaderManager()
    all_documents = []

    # 1. 加载本地文件
    print("\n1. 加载本地文件...")
    local_docs = manager.load_from_directory("../chat/data")
    all_documents.extend(local_docs)

    # 2. 加载 Jira（如果配置）
    # if "jira" in manager.readers:
    #     print("\n2. 加载 Jira 问题...")
    #     jira_docs = manager.load_with_reader("jira", query="project=PROJ")
    #     all_documents.extend(jira_docs)

    # 3. 加载 Confluence（如果配置）
    # if "confluence" in manager.readers:
    #     print("\n3. 加载 Confluence 页面...")
    #     confluence_docs = manager.load_with_reader("confluence", space_key="SPACE")
    #     all_documents.extend(confluence_docs)

    print(f"\n总共加载了 {len(all_documents)} 个文档")

    # 应用统一的数据治理
    print("\n应用数据治理...")
    quality_checker = DataQualityChecker()
    validated_docs, metrics = quality_checker.validate(all_documents)

    pii_filter = PIIFilter()
    safe_docs = pii_filter.filter(validated_docs)

    print(f"治理后剩余 {len(safe_docs)} 个文档")

    # 创建统一索引
    print("\n创建统一索引...")
    index = VectorStoreIndex.from_documents(safe_docs)
    print("完成！所有数据源已集成到一个索引中")

    return index


async def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("LlamaIndex Readers + 数据治理 - 完整示例")
    print("=" * 80)

    # 示例 1: 基础加载
    await example_basic()

    # 示例 2: 数据治理
    await example_with_governance()

    # 示例 3: 创建索引
    # await example_create_index()

    # 示例 4: Jira & Confluence
    await example_jira_confluence()

    # 示例 5: 多数据源
    # await example_multi_source()

    print("\n" + "=" * 80)
    print("示例运行完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
