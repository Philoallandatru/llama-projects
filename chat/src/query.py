"""
查询引擎模块

创建和配置 LlamaIndex 查询引擎
"""
from llama_index.core import VectorStoreIndex


def create_query_engine(index: VectorStoreIndex, top_k: int = 3, streaming: bool = True):
    """
    创建查询引擎

    Args:
        index: 向量索引
        top_k: 返回的相关文档数量
        streaming: 是否启用流式响应

    Returns:
        查询引擎实例
    """
    return index.as_query_engine(
        similarity_top_k=top_k,
        response_mode="compact",
        streaming=streaming
    )
