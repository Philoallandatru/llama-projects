# LLM Wiki Layer - Detailed Design

## Overview

The LLM Wiki layer transforms structured data from Jira and Confluence into a navigable knowledge graph using [llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler). It runs as an independent system alongside the existing DataSource layer, providing concept-based exploration complementary to DataSource's vector search.

## Architecture Decisions

### 1. Dual-Path Architecture

```
Raw Data Sources (Jira/Confluence)
         ↓                    ↓
    DataSource          LLM Wiki
    (Vector Search)     (Knowledge Graph)
         ↓                    ↓
    Application Layer
    (Use both based on scenario)
```

**Key Points:**
- Both systems fetch directly from raw data sources
- No dependency between DataSource and LLM Wiki
- DataSource optimized for fast retrieval (vector + BM25)
- LLM Wiki optimized for concept exploration (knowledge graph)

### 2. Code Reuse Strategy

LLM Wiki reuses DataSource's API client code:
- `datasource.sources.jira.JiraDataSource` - Jira API client
- `datasource.sources.confluence.ConfluenceDataSource` - Confluence API client

**Why:** Avoid duplicating authentication, pagination, rate limiting, error handling logic.

**How:** Import as library dependency, use only the data fetching methods.

### 3. Data Format Conversion

**Responsibility:** LLM Wiki layer converts JSON → narrative Markdown

**Rationale:**
- llm-wiki-compiler expects human-readable text for concept extraction
- Structured JSON (fields, arrays, metadata) is not suitable for LLM concept extraction
- Conversion logic is specific to wiki generation needs

**Location:** `llmwiki/converters/` module

### 4. Incremental Sync Strategy

**Hybrid approach:**
1. **Fetch phase:** Use timestamp-based incremental fetching from DataSource APIs
2. **Compile phase:** llm-wiki-compiler's SHA-256 hash detection handles change detection

**Benefits:**
- Minimize API calls (only fetch changed items)
- Avoid redundant compilation (hash detects actual content changes)
- Resilient to metadata-only updates

### 5. System Independence

**Design:** Two completely independent systems with optional coordination scripts

**Rationale:**
- Different update frequencies (DataSource: real-time, Wiki: periodic)
- Different use cases (search vs exploration)
- Simpler deployment and maintenance

**Coordination:** Optional convenience scripts for common workflows

## Component Design

### Directory Structure

```
llmwiki/
├── __init__.py
├── config.py              # Configuration management
├── cli.py                 # Command-line interface
├── sync.py                # Incremental sync orchestration
├── converters/
│   ├── __init__.py
│   ├── base.py           # Base converter interface
│   ├── jira.py           # Jira JSON → Markdown
│   └── confluence.py     # Confluence JSON → Markdown
├── sources/              # Output: Markdown files for compilation
│   ├── jira/
│   └── confluence/
└── wiki/                 # Output: Compiled wiki from llm-wiki-compiler
    ├── concepts/
    └── index.md
```

### Configuration (`config.py`)

```python
@dataclass
class LLMWikiConfig:
    # Data source connections (reuse DataSource config)
    jira_url: str
    jira_username: str
    jira_api_token: str
    confluence_url: str
    confluence_username: str
    confluence_api_token: str
    
    # Sync settings
    sync_interval_hours: int = 24
    last_sync_timestamp: Optional[datetime] = None
    
    # llm-wiki-compiler settings
    sources_dir: Path = Path("llmwiki/sources")
    wiki_dir: Path = Path("llmwiki/wiki")
    llm_provider: str = "anthropic"  # or "openai"
    llm_model: str = "claude-sonnet-4"
    
    # Conversion settings
    include_comments: bool = True
    include_attachments: bool = False
    max_description_length: int = 5000
```

### Sync Orchestrator (`sync.py`)

```python
class WikiSyncOrchestrator:
    """Coordinates incremental sync from data sources to wiki compilation."""
    
    def __init__(self, config: LLMWikiConfig):
        self.config = config
        self.jira_client = JiraDataSource(...)
        self.confluence_client = ConfluenceDataSource(...)
        self.jira_converter = JiraConverter()
        self.confluence_converter = ConfluenceConverter()
    
    async def sync(self, force_full: bool = False):
        """Run incremental sync and compilation."""
        # 1. Fetch changed items since last sync
        last_sync = None if force_full else self.config.last_sync_timestamp
        
        jira_issues = await self.jira_client.fetch_updated_since(last_sync)
        confluence_pages = await self.confluence_client.fetch_updated_since(last_sync)
        
        # 2. Convert to Markdown and write to sources/
        for issue in jira_issues:
            md_content = self.jira_converter.convert(issue)
            output_path = self.config.sources_dir / "jira" / f"{issue.key}.md"
            output_path.write_text(md_content)
        
        for page in confluence_pages:
            md_content = self.confluence_converter.convert(page)
            output_path = self.config.sources_dir / "confluence" / f"{page.id}.md"
            output_path.write_text(md_content)
        
        # 3. Run llm-wiki-compiler (handles hash-based change detection)
        await self.compile_wiki()
        
        # 4. Update last sync timestamp
        self.config.last_sync_timestamp = datetime.now()
        self.save_config()
    
    async def compile_wiki(self):
        """Invoke llm-wiki-compiler on sources/ directory."""
        # Call llm-wiki-compiler CLI or use as library
        subprocess.run([
            "npx", "llm-wiki-compiler",
            "--sources", str(self.config.sources_dir),
            "--output", str(self.config.wiki_dir),
            "--provider", self.config.llm_provider,
            "--model", self.config.llm_model
        ])
```

### Converters

#### Base Converter (`converters/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseConverter(ABC):
    """Base class for JSON to Markdown converters."""
    
    @abstractmethod
    def convert(self, data: Dict[str, Any]) -> str:
        """Convert structured data to narrative Markdown."""
        pass
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as YAML frontmatter."""
        lines = ["---"]
        for key, value in metadata.items():
            lines.append(f"{key}: {value}")
        lines.append("---\n")
        return "\n".join(lines)
```

#### Jira Converter (`converters/jira.py`)

```python
class JiraConverter(BaseConverter):
    """Converts Jira issues to narrative Markdown."""
    
    def convert(self, issue: Dict[str, Any]) -> str:
        """
        Convert Jira issue JSON to narrative Markdown.
        
        Input: Jira issue JSON from API
        Output: Human-readable Markdown suitable for concept extraction
        """
        fields = issue["fields"]
        
        # Metadata frontmatter
        metadata = {
            "source": "jira",
            "key": issue["key"],
            "type": fields.get("issuetype", {}).get("name"),
            "status": fields.get("status", {}).get("name"),
            "created": fields.get("created"),
            "updated": fields.get("updated"),
            "url": f"{self.jira_url}/browse/{issue['key']}"
        }
        
        # Narrative content
        content = [
            self._format_metadata(metadata),
            f"# {issue['key']}: {fields.get('summary', 'Untitled')}",
            "",
            "## Overview",
            "",
            f"This is a {fields.get('issuetype', {}).get('name', 'issue')} "
            f"currently in {fields.get('status', {}).get('name', 'unknown')} status.",
            ""
        ]
        
        # Description
        if description := fields.get("description"):
            content.extend([
                "## Description",
                "",
                self._convert_adf_to_markdown(description),
                ""
            ])
        
        # Key relationships
        if assignee := fields.get("assignee"):
            content.append(f"**Assigned to:** {assignee.get('displayName')}")
        
        if reporter := fields.get("reporter"):
            content.append(f"**Reported by:** {reporter.get('displayName')}")
        
        if priority := fields.get("priority"):
            content.append(f"**Priority:** {priority.get('name')}")
        
        content.append("")
        
        # Links and relationships
        if issuelinks := fields.get("issuelinks"):
            content.extend(["## Related Issues", ""])
            for link in issuelinks:
                if "outwardIssue" in link:
                    related = link["outwardIssue"]
                    content.append(
                        f"- {link['type']['outward']}: "
                        f"[[{related['key']}]] - {related['fields']['summary']}"
                    )
                elif "inwardIssue" in link:
                    related = link["inwardIssue"]
                    content.append(
                        f"- {link['type']['inward']}: "
                        f"[[{related['key']}]] - {related['fields']['summary']}"
                    )
            content.append("")
        
        # Comments (if enabled)
        if self.config.include_comments and (comments := fields.get("comment", {}).get("comments")):
            content.extend(["## Discussion", ""])
            for comment in comments[:10]:  # Limit to recent 10
                author = comment.get("author", {}).get("displayName", "Unknown")
                body = self._convert_adf_to_markdown(comment.get("body", ""))
                content.extend([
                    f"**{author}** commented:",
                    "",
                    body,
                    "",
                    "---",
                    ""
                ])
        
        return "\n".join(content)
    
    def _convert_adf_to_markdown(self, adf: Dict[str, Any]) -> str:
        """Convert Atlassian Document Format to Markdown."""
        # Simplified conversion - handle basic text, paragraphs, lists
        # Full implementation would handle all ADF node types
        if isinstance(adf, str):
            return adf
        
        # Handle ADF structure
        if adf.get("type") == "doc":
            return "\n\n".join(
                self._convert_adf_node(node) 
                for node in adf.get("content", [])
            )
        
        return str(adf)
    
    def _convert_adf_node(self, node: Dict[str, Any]) -> str:
        """Convert single ADF node to Markdown."""
        node_type = node.get("type")
        
        if node_type == "paragraph":
            return "".join(
                self._convert_adf_text(item) 
                for item in node.get("content", [])
            )
        elif node_type == "bulletList":
            return "\n".join(
                f"- {self._convert_adf_node(item)}"
                for item in node.get("content", [])
            )
        elif node_type == "orderedList":
            return "\n".join(
                f"{i+1}. {self._convert_adf_node(item)}"
                for i, item in enumerate(node.get("content", []))
            )
        elif node_type == "listItem":
            return "".join(
                self._convert_adf_node(item)
                for item in node.get("content", [])
            )
        elif node_type == "codeBlock":
            code = "".join(
                item.get("text", "")
                for item in node.get("content", [])
            )
            lang = node.get("attrs", {}).get("language", "")
            return f"```{lang}\n{code}\n```"
        
        return ""
    
    def _convert_adf_text(self, text_node: Dict[str, Any]) -> str:
        """Convert ADF text node with marks to Markdown."""
        text = text_node.get("text", "")
        marks = text_node.get("marks", [])
        
        for mark in marks:
            mark_type = mark.get("type")
            if mark_type == "strong":
                text = f"**{text}**"
            elif mark_type == "em":
                text = f"*{text}*"
            elif mark_type == "code":
                text = f"`{text}`"
            elif mark_type == "link":
                href = mark.get("attrs", {}).get("href", "")
                text = f"[{text}]({href})"
        
        return text
```

#### Confluence Converter (`converters/confluence.py`)

```python
class ConfluenceConverter(BaseConverter):
    """Converts Confluence pages to narrative Markdown."""
    
    def convert(self, page: Dict[str, Any]) -> str:
        """
        Convert Confluence page JSON to narrative Markdown.
        
        Input: Confluence page JSON from API
        Output: Human-readable Markdown suitable for concept extraction
        """
        # Metadata frontmatter
        metadata = {
            "source": "confluence",
            "id": page["id"],
            "title": page["title"],
            "space": page.get("space", {}).get("key"),
            "created": page.get("history", {}).get("createdDate"),
            "updated": page.get("version", {}).get("when"),
            "url": f"{self.confluence_url}/pages/viewpage.action?pageId={page['id']}"
        }
        
        # Narrative content
        content = [
            self._format_metadata(metadata),
            f"# {page['title']}",
            ""
        ]
        
        # Space and hierarchy context
        if space := page.get("space"):
            content.append(f"*From {space.get('name')} space*")
            content.append("")
        
        if ancestors := page.get("ancestors"):
            breadcrumb = " > ".join(a.get("title", "") for a in ancestors)
            content.append(f"**Location:** {breadcrumb}")
            content.append("")
        
        # Page body
        if body := page.get("body", {}).get("storage", {}).get("value"):
            md_body = self._convert_confluence_storage_to_markdown(body)
            content.extend([md_body, ""])
        
        # Labels/tags
        if labels := page.get("metadata", {}).get("labels", {}).get("results"):
            tags = ", ".join(f"#{label['name']}" for label in labels)
            content.extend([
                "---",
                "",
                f"**Tags:** {tags}",
                ""
            ])
        
        # Child pages (as links)
        if children := page.get("children", {}).get("page", {}).get("results"):
            content.extend(["## Related Pages", ""])
            for child in children:
                content.append(f"- [[{child['title']}]]")
            content.append("")
        
        return "\n".join(content)
    
    def _convert_confluence_storage_to_markdown(self, html: str) -> str:
        """Convert Confluence storage format (XHTML) to Markdown."""
        # Use html2text or similar library for robust conversion
        # Simplified implementation:
        import re
        from html.parser import HTMLParser
        
        # Basic HTML to Markdown conversion
        md = html
        
        # Headers
        for i in range(1, 7):
            md = re.sub(f'<h{i}>(.*?)</h{i}>', f'{"#" * i} \\1\n', md)
        
        # Bold/italic
        md = re.sub(r'<strong>(.*?)</strong>', r'**\1**', md)
        md = re.sub(r'<em>(.*?)</em>', r'*\1*', md)
        
        # Links
        md = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', md)
        
        # Code
        md = re.sub(r'<code>(.*?)</code>', r'`\1`', md)
        
        # Lists
        md = re.sub(r'<ul>(.*?)</ul>', r'\1', md, flags=re.DOTALL)
        md = re.sub(r'<li>(.*?)</li>', r'- \1\n', md)
        
        # Paragraphs
        md = re.sub(r'<p>(.*?)</p>', r'\1\n\n', md)
        
        # Remove remaining tags
        md = re.sub(r'<[^>]+>', '', md)
        
        return md.strip()
```

### CLI Interface (`cli.py`)

```python
import click
from pathlib import Path

@click.group()
def cli():
    """LLM Wiki - Knowledge graph from Jira and Confluence."""
    pass

@cli.command()
@click.option("--force-full", is_flag=True, help="Force full sync (ignore timestamps)")
def sync(force_full: bool):
    """Sync data sources and compile wiki."""
    config = LLMWikiConfig.load()
    orchestrator = WikiSyncOrchestrator(config)
    
    click.echo("Starting sync...")
    asyncio.run(orchestrator.sync(force_full=force_full))
    click.echo("Sync complete!")

@cli.command()
def compile():
    """Compile wiki from existing sources/ directory."""
    config = LLMWikiConfig.load()
    orchestrator = WikiSyncOrchestrator(config)
    
    click.echo("Compiling wiki...")
    asyncio.run(orchestrator.compile_wiki())
    click.echo("Compilation complete!")

@cli.command()
@click.argument("query")
def search(query: str):
    """Search the compiled wiki."""
    config = LLMWikiConfig.load()
    
    # Use llm-wiki-compiler's retrieval API
    results = retrieve_from_wiki(
        query=query,
        wiki_dir=config.wiki_dir,
        top_k=5
    )
    
    for result in results:
        click.echo(f"\n## {result['title']}")
        click.echo(f"Score: {result['score']:.3f}")
        click.echo(result['content'][:200] + "...")

if __name__ == "__main__":
    cli()
```

## Integration Patterns

### Scenario-Based Usage

**Fast Retrieval (Use DataSource):**
```python
# User asks: "Show me recent bugs in project X"
from datasource import DataSourceManager

manager = DataSourceManager()
results = await manager.query(
    "recent bugs in project X",
    sources=["jira"],
    limit=10
)
```

**Concept Exploration (Use LLM Wiki):**
```python
# User asks: "What are the main architectural patterns in our system?"
from llmwiki import retrieve_from_wiki

results = retrieve_from_wiki(
    query="architectural patterns",
    wiki_dir="llmwiki/wiki",
    top_k=5
)

# Results include concept pages with relationships
for result in results:
    print(f"Concept: {result['title']}")
    print(f"Related: {result['wikilinks']}")
```

### Convenience Scripts

**Full Sync Script (`scripts/sync_all.sh`):**
```bash
#!/bin/bash
# Sync both DataSource and LLM Wiki

echo "Syncing DataSource..."
cd datasource && python -m datasource.cli sync

echo "Syncing LLM Wiki..."
cd ../llmwiki && python -m llmwiki.cli sync

echo "All systems synced!"
```

**Scheduled Sync (cron):**
```cron
# Sync DataSource every hour
0 * * * * cd /path/to/datasource && python -m datasource.cli sync

# Sync LLM Wiki daily at 2 AM
0 2 * * * cd /path/to/llmwiki && python -m llmwiki.cli sync
```

## Data Flow

```
1. Fetch Phase (Incremental)
   ┌─────────────────────────────────────────┐
   │ JiraDataSource.fetch_updated_since()    │
   │ ConfluenceDataSource.fetch_updated_since()│
   └─────────────────┬───────────────────────┘
                     │ JSON data
                     ↓
2. Conversion Phase
   ┌─────────────────────────────────────────┐
   │ JiraConverter.convert()                 │
   │ ConfluenceConverter.convert()           │
   └─────────────────┬───────────────────────┘
                     │ Markdown files
                     ↓
3. File System Injection
   ┌─────────────────────────────────────────┐
   │ Write to llmwiki/sources/               │
   │   - jira/PROJ-123.md                    │
   │   - confluence/12345.md                 │
   └─────────────────┬───────────────────────┘
                     │
                     ↓
4. Compilation Phase (llm-wiki-compiler)
   ┌─────────────────────────────────────────┐
   │ SHA-256 hash detection                  │
   │ LLM concept extraction                  │
   │ Wiki page generation                    │
   │ [[Wikilink]] resolution                 │
   └─────────────────┬───────────────────────┘
                     │ Wiki pages
                     ↓
5. Output
   ┌─────────────────────────────────────────┐
   │ llmwiki/wiki/                           │
   │   - concepts/Authentication.md          │
   │   - concepts/API_Design.md              │
   │   - index.md                            │
   └─────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. Create package structure (`llmwiki/`)
2. Implement configuration management (`config.py`)
3. Set up llm-wiki-compiler integration
4. Create base converter interface

### Phase 2: Data Conversion
1. Implement Jira converter with ADF parsing
2. Implement Confluence converter with storage format parsing
3. Add unit tests for converters
4. Validate output Markdown quality

### Phase 3: Sync Orchestration
1. Implement `WikiSyncOrchestrator`
2. Add timestamp-based incremental fetching
3. Integrate with llm-wiki-compiler CLI
4. Add error handling and logging

### Phase 4: CLI and Tooling
1. Implement CLI commands (`sync`, `compile`, `search`)
2. Create convenience scripts
3. Add configuration validation
4. Write usage documentation

### Phase 5: Testing and Validation
1. End-to-end testing with real data
2. Performance testing (large datasets)
3. Validate concept extraction quality
4. Document best practices

## Dependencies

**Python:**
- `datasource` (local package) - API clients
- `click` - CLI framework
- `pydantic` - Configuration validation
- `aiohttp` - Async HTTP (if needed)
- `html2text` - HTML to Markdown conversion

**Node.js:**
- `llm-wiki-compiler` - Core wiki compilation engine

**External Services:**
- Jira API
- Confluence API
- LLM provider (Anthropic Claude or OpenAI)

## Configuration Example

```yaml
# llmwiki/config.yaml
jira:
  url: https://your-domain.atlassian.net
  username: your-email@example.com
  api_token: ${JIRA_API_TOKEN}

confluence:
  url: https://your-domain.atlassian.net/wiki
  username: your-email@example.com
  api_token: ${CONFLUENCE_API_TOKEN}

sync:
  interval_hours: 24
  include_comments: true
  include_attachments: false

llm:
  provider: anthropic
  model: claude-sonnet-4
  api_key: ${ANTHROPIC_API_KEY}

paths:
  sources: llmwiki/sources
  wiki: llmwiki/wiki
```

## Future Enhancements

1. **Multi-source support:** Add GitHub, Slack, Google Docs
2. **Custom concept extraction:** Fine-tune prompts for domain-specific concepts
3. **Real-time updates:** WebSocket-based incremental updates
4. **Visualization:** Graph visualization of concept relationships
5. **Search UI:** Web interface for wiki exploration
6. **Analytics:** Track concept evolution over time
