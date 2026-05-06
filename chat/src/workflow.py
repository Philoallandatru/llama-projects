import logging
from dotenv import load_dotenv

from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.settings import Settings

from src.index import get_index
from src.query import get_query_engine_tool
from src.citation import CITATION_SYSTEM_PROMPT, enable_citation
from src.settings import init_settings
from src.llmwiki_integration import create_llmwiki_tool

logger = logging.getLogger(__name__)


def create_workflow() -> AgentWorkflow:
    load_dotenv()
    init_settings()

    # 准备工具列表
    tools = []

    # 添加 datasource 查询工具
    index = get_index()
    if index is None:
        logger.warning(
            "Index not found! Datasource query tool will not be available. "
            "Run `uv run generate` to index the data."
        )
    else:
        query_tool = enable_citation(get_query_engine_tool(index=index))
        tools.append(query_tool)
        logger.info("Added datasource query tool")

    # 添加 llmwiki 查询工具
    try:
        llmwiki_tool = create_llmwiki_tool()
        tools.append(llmwiki_tool)
        logger.info("Added llmwiki query tool")
    except Exception as e:
        logger.warning(f"Failed to create llmwiki tool: {e}")
        logger.warning("LLM Wiki queries will not be available")

    if not tools:
        raise RuntimeError(
            "No query tools available! Please set up at least one data source:\n"
            "- For datasource: run `uv run generate`\n"
            "- For llmwiki: run `cd ../llmwiki && python -m llmwiki sync && python -m llmwiki compile`"
        )

    # Define the system prompt for the agent
    system_prompt = """You are a helpful assistant with access to multiple knowledge sources:

1. Datasource query tool: Query indexed documents from various data sources (Jira, Confluence, local files)
2. LLM Wiki query tool: Query the compiled wiki knowledge base with advanced retrieval

Choose the appropriate tool based on the user's question. You can use both tools if needed to provide comprehensive answers."""
    system_prompt += CITATION_SYSTEM_PROMPT

    return AgentWorkflow.from_tools_or_functions(
        tools_or_functions=tools,
        llm=Settings.llm,
        system_prompt=system_prompt,
    )


workflow = create_workflow()
