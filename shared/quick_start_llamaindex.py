"""
快速开始 - 使用 LlamaIndex Readers
"""
from llama_index.core import VectorStoreIndex, Settings
from readers.manager import ReaderManager
from governance.quality import DataQualityChecker
from governance.security import PIIFilter


def quick_start():
    """5 分钟快速开始"""

    # 1. 创建 Reader 管理器
    manager = ReaderManager()

    # 2. 加载文档（自动识别格式）
    documents = manager.load_from_directory(
        directory="../chat/data",
        recursive=True
    )

    print(f"加载了 {len(documents)} 个文档")

    # 3. 可选：应用数据治理
    # 质量检查
    quality_checker = DataQualityChecker()
    validated_docs, metrics = quality_checker.validate(documents)

    # PII 过滤
    pii_filter = PIIFilter()
    safe_docs = pii_filter.filter(validated_docs)

    print(f"治理后: {len(safe_docs)} 个文档")

    # 4. 创建索引
    index = VectorStoreIndex.from_documents(
        safe_docs,
        embed_model=Settings.embed_model
    )

    # 5. 查询
    query_engine = index.as_query_engine()
    response = query_engine.query("文档的主要内容是什么？")

    print(f"\n查询结果: {response}")

    return index


if __name__ == "__main__":
    quick_start()
