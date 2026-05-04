"""
LLM Wiki Layer - Knowledge graph generation from Jira and Confluence.

This package transforms structured data from Jira and Confluence into a navigable
knowledge graph using llm-wiki-compiler. It provides:

- Incremental sync from data sources
- JSON to narrative Markdown conversion
- Integration with llm-wiki-compiler for concept extraction
- CLI tools for sync and search operations
"""

__version__ = "0.1.0"

from llmwiki.config import LLMWikiConfig
from llmwiki.sync import WikiSyncOrchestrator
from llmwiki.retrieval import WikiRetrieval, QueryResult, query_wiki

__all__ = [
    "LLMWikiConfig",
    "WikiSyncOrchestrator",
    "WikiRetrieval",
    "QueryResult",
    "query_wiki",
]
