"""Bridge to llm-wiki-compiler's retrieval engine."""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from llmwiki.config import LLMWikiConfig


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class ChunkCitation:
    """A chunk citation from retrieval."""
    slug: str
    title: str
    chunk_index: int
    score: float
    text: str


@dataclass
class RetrievalDebug:
    """Debug information from retrieval pipeline."""
    pages: list[dict[str, any]]
    chunks: list[ChunkCitation]
    used_chunks: bool
    reranked: bool


@dataclass
class QueryResult:
    """Result from wiki query."""
    answer: str
    selected_pages: list[str]
    reasoning: str
    saved_slug: Optional[str] = None
    debug: Optional[RetrievalDebug] = None


@dataclass
class QueryOptions:
    """Options for wiki query."""
    save: bool = False
    debug: bool = False
    top_k: int = 20
    rerank_keep: int = 5


class WikiRetrieval:
    """Python interface to llm-wiki-compiler's retrieval engine."""

    def __init__(self, config: LLMWikiConfig):
        """
        Initialize retrieval interface.

        Args:
            config: Wiki configuration
        """
        self.config = config
        self.root = config.sources_dir.parent

    def query(
        self,
        question: str,
        options: Optional[QueryOptions] = None,
    ) -> QueryResult:
        """
        Query the wiki using llm-wiki-compiler's retrieval engine.

        This uses the full two-stage retrieval pipeline:
        1. Chunk-level embeddings → BM25 reranking → page selection
        2. Load full pages + chunk excerpts → LLM answer generation

        Args:
            question: Natural language question
            options: Query options (defaults to QueryOptions())

        Returns:
            QueryResult with answer, selected pages, and optional debug info
        """
        if options is None:
            options = QueryOptions()

        # Create a Node.js script that calls the programmatic API
        script = self._build_query_script(question, options)

        # Write script to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mjs", delete=False) as f:
            f.write(script)
            script_path = f.name

        try:
            # Execute Node.js script
            result = subprocess.run(
                ["node", script_path],
                capture_output=True,
                text=True,
                cwd=str(self.root),
                env=self._build_env(),
            )

            if result.returncode != 0:
                raise RuntimeError(f"Query failed: {result.stderr}")

            # Parse JSON result
            output = result.stdout.strip()

            # Split streaming output from JSON result
            # The script outputs answer tokens to stderr, JSON to stdout
            data = json.loads(output)

            return self._parse_result(data)

        finally:
            # Clean up temp file
            Path(script_path).unlink(missing_ok=True)

    def _build_query_script(
        self,
        question: str,
        options: QueryOptions,
    ) -> str:
        """Build Node.js script that calls llm-wiki-compiler programmatically."""
        # Escape question for JSON
        question_json = json.dumps(question)

        return f"""
import {{ generateAnswer }} from 'llm-wiki-compiler/dist/commands/query.js';
import {{ CHUNK_TOP_K, CHUNK_RERANK_KEEP }} from 'llm-wiki-compiler/dist/utils/constants.js';

// Override constants for this query
const originalTopK = CHUNK_TOP_K;
const originalRerank = CHUNK_RERANK_KEEP;

// Monkey-patch constants (not ideal but llm-wiki-compiler doesn't expose config)
Object.defineProperty(await import('llm-wiki-compiler/dist/utils/constants.js'), 'CHUNK_TOP_K', {{
  value: {options.top_k},
  writable: false
}});
Object.defineProperty(await import('llm-wiki-compiler/dist/utils/constants.js'), 'CHUNK_RERANK_KEEP', {{
  value: {options.rerank_keep},
  writable: false
}});

const root = process.cwd();
const question = {question_json};

try {{
  const result = await generateAnswer(root, question, {{
    save: {str(options.save).lower()},
    debug: {str(options.debug).lower()},
    onToken: (text) => {{
      // Stream tokens to stderr so they don't interfere with JSON output
      process.stderr.write(text);
    }},
  }});

  // Output structured result as JSON to stdout
  console.log(JSON.stringify({{
    answer: result.answer,
    selectedPages: result.selectedPages,
    reasoning: result.reasoning,
    saved: result.saved,
    debug: result.debug ? {{
      pages: result.debug.pages,
      chunks: result.debug.chunks,
      usedChunks: result.debug.usedChunks,
      reranked: result.debug.reranked,
    }} : null,
  }}));
}} catch (err) {{
  console.error('Query error:', err.message);
  process.exit(1);
}}
"""

    def _build_env(self) -> dict[str, str]:
        """Build environment variables for Node.js process."""
        import os

        env = os.environ.copy()

        # Set LLM provider config using enum
        provider = LLMProvider(self.config.llm_provider)
        if provider == LLMProvider.ANTHROPIC:
            env["ANTHROPIC_API_KEY"] = self.config.llm_api_key
        elif provider == LLMProvider.OPENAI:
            env["OPENAI_API_KEY"] = self.config.llm_api_key

        return env

    def _parse_result(self, data: dict) -> QueryResult:
        """Parse JSON result from Node.js script."""
        debug = None
        if data.get("debug"):
            debug_data = data["debug"]
            chunks = [
                ChunkCitation(
                    slug=c["slug"],
                    title=c["title"],
                    chunk_index=c["chunkIndex"],
                    score=c["score"],
                    text=c["text"],
                )
                for c in debug_data.get("chunks", [])
            ]
            debug = RetrievalDebug(
                pages=debug_data.get("pages", []),
                chunks=chunks,
                used_chunks=debug_data.get("usedChunks", False),
                reranked=debug_data.get("reranked", False),
            )

        return QueryResult(
            answer=data["answer"],
            selected_pages=data["selectedPages"],
            reasoning=data["reasoning"],
            saved_slug=data.get("saved"),
            debug=debug,
        )


def query_wiki(
    config: LLMWikiConfig,
    question: str,
    options: Optional[QueryOptions] = None,
) -> QueryResult:
    """
    Convenience function to query the wiki.

    Args:
        config: Wiki configuration
        question: Natural language question
        options: Query options (defaults to QueryOptions())

    Returns:
        QueryResult with answer and metadata
    """
    retrieval = WikiRetrieval(config)
    return retrieval.query(question, options=options)
