"""
查询引擎模块

创建和配置 LlamaIndex 查询引擎
"""
from llama_index.core import VectorStoreIndex
from llama_index.core.tools import QueryEngineTool


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


def get_query_engine_tool(index: VectorStoreIndex, top_k: int = 3) -> QueryEngineTool:
    """
    创建查询引擎工具，用于 agent 调用

    Args:
        index: 向量索引
        top_k: 返回的相关文档数量

    Returns:
        QueryEngineTool 实例
    """
    query_engine = create_query_engine(index, top_k=top_k, streaming=False)

    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="datasource_query",
        description=(
            "Query indexed documents from various data sources including Jira issues, "
            "Confluence pages, and local files. Use this tool to search for specific "
            "information in the indexed knowledge base."
        )
    )
