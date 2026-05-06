"""
LLM Wiki 集成模块

将 llmwiki 作为知识源集成到 chat 项目中
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# 添加 llmwiki 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "llmwiki"))

from llmwiki.config import LLMWikiConfig
from llmwiki.retrieval import query_wiki, QueryOptions, QueryResult

logger = logging.getLogger(__name__)


class LLMWikiIntegration:
    """LLM Wiki 集成类"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化 LLM Wiki 集成

        Args:
            config_path: llmwiki 配置文件路径（默认: ../llmwiki/config.yaml）
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "llmwiki" / "config.yaml"

        try:
            self.config = LLMWikiConfig.load(config_path)
            logger.info(f"Loaded llmwiki config from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load llmwiki config: {e}")
            raise

    def query(
        self,
        question: str,
        top_k: int = 20,
        rerank_keep: int = 5,
        debug: bool = False,
    ) -> QueryResult:
        """
        查询 LLM Wiki

        Args:
            question: 用户问题
            top_k: 初始检索的 chunk 数量
            rerank_keep: BM25 重排后保留的 chunk 数量
            debug: 是否返回调试信息

        Returns:
            QueryResult 包含答案、选中的页面和引用信息
        """
        options = QueryOptions(
            save=False,
            debug=debug,
            top_k=top_k,
            rerank_keep=rerank_keep,
        )

        try:
            result = query_wiki(
                config=self.config,
                question=question,
                options=options,
            )
            logger.info(f"Query completed: {len(result.selected_pages)} pages selected")
            return result

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def get_citations(self, result: QueryResult) -> list[dict]:
        """
        从查询结果中提取引用信息

        Args:
            result: 查询结果

        Returns:
            引用列表，每个引用包含 page_slug, title, score 等信息
        """
        citations = []

        if result.debug and result.debug.chunks:
            # 使用 debug 信息中的 chunk 引用
            for chunk in result.debug.chunks:
                citations.append({
                    "page_slug": chunk.slug,
                    "title": chunk.title,
                    "chunk_index": chunk.chunk_index,
                    "score": chunk.score,
                    "text": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                })
        else:
            # 如果没有 debug 信息，使用选中的页面
            for page_slug in result.selected_pages:
                citations.append({
                    "page_slug": page_slug,
                    "title": page_slug.replace("-", " ").title(),
                    "score": 1.0,
                })

        return citations


def create_llmwiki_tool():
    """
    创建 LLM Wiki 查询工具（用于 LlamaIndex Agent）

    Returns:
        FunctionTool 实例
    """
    from llama_index.core.tools import FunctionTool
    import uuid

    integration = LLMWikiIntegration()

    def query_llmwiki(question: str) -> str:
        """
        Query the LLM Wiki knowledge base for information about Jira issues, Confluence pages, and technical documentation.

        Args:
            question: The question to ask the wiki

        Returns:
            Answer from the wiki with relevant citations in [citation:id] format
        """
        try:
            result = integration.query(question, debug=True)

            # 构建带引用的答案
            answer = result.answer

            # 添加引用信息（使用与 datasource 相同的 [citation:id] 格式）
            if result.debug and result.debug.chunks:
                # 为每个 chunk 生成唯一的 citation_id
                answer += "\n\nSources from LLM Wiki:\n"
                for chunk in result.debug.chunks:
                    citation_id = str(uuid.uuid4())
                    answer += f"[citation:{citation_id}] {chunk.title} (chunk {chunk.chunk_index}, score: {chunk.score:.3f})\n"
            elif result.selected_pages:
                # 如果没有 debug 信息，使用页面列表
                answer += "\n\nSources from LLM Wiki:\n"
                for page in result.selected_pages:
                    citation_id = str(uuid.uuid4())
                    answer += f"[citation:{citation_id}] {page}\n"

            return answer

        except Exception as e:
            logger.error(f"LLM Wiki query failed: {e}")
            return f"Error querying wiki: {str(e)}"

    return FunctionTool.from_defaults(
        fn=query_llmwiki,
        name="query_llmwiki",
        description=(
            "Query the LLM Wiki knowledge base for information about Jira issues, Confluence pages, and technical documentation. "
            "Use this when the user asks about project-specific information, bug reports, or technical specifications. "
            "The output will include citations with the format [citation:id] for each source."
        ),
    )
