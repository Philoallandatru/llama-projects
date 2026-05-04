# LLM Wiki Layer

Transform Jira and Confluence data into a navigable knowledge graph using [llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler).

## Overview

The LLM Wiki layer sits alongside the DataSource layer, providing concept-based knowledge exploration complementary to vector search:

```
Raw Data (Jira/Confluence)
    ├─→ DataSource (fast vector search)
    └─→ LLM Wiki (concept knowledge graph)
```

## Features

- **Incremental Sync**: Only fetch and process changed items
- **Narrative Conversion**: Transform structured JSON into human-readable Markdown
- **Concept Extraction**: LLM automatically identifies and links concepts
- **Knowledge Accumulation**: Query results can be saved back to the wiki
- **Dual Retrieval**: Vector similarity + BM25 keyword matching

## Quick Start

### 1. Installation

```bash
# Install Python dependencies
cd llmwiki
pip install -r requirements.txt

# Install llm-wiki-compiler (Node.js)
npm install -g llm-wiki-compiler
```

### 2. Configuration

```bash
# Initialize directory structure
python -m llmwiki.cli init

# Edit config file
vim llmwiki/config.yaml
```

Set environment variables:
```bash
export JIRA_API_TOKEN=your_token
export CONFLUENCE_API_TOKEN=your_token
export ANTHROPIC_API_KEY=your_key
```

### 3. First Sync

```bash
# Full sync (first time)
python -m llmwiki.cli sync --force

# Check status
python -m llmwiki.cli status
```

### 4. Query the Wiki

```bash
# Search for concepts
python -m llmwiki.cli query "authentication patterns"

# Save query result as wiki page
python -m llmwiki.cli query "API design principles" --save
```

## Architecture

### Data Flow

```
1. Fetch (Incremental)
   Jira/Confluence API → JSON data
   
2. Convert
   JSON → Narrative Markdown
   
3. Write
   sources/jira-PROJ-123.md
   sources/confluence-12345.md
   
4. Compile (llm-wiki-compiler)
   SHA-256 hash detection
   → LLM concept extraction
   → wiki/concepts/*.md
   
5. Query
   Vector + BM25 hybrid search
```

### Components

- **config.py**: Configuration management with env var substitution
- **sync.py**: Incremental sync orchestrator
- **converters/**: JSON → Markdown converters
  - `jira.py`: Jira issues with full ADF support
  - `confluence.py`: Confluence pages with storage format parsing
- **cli.py**: Command-line interface

## Usage

### Sync Commands

```bash
# Incremental sync (default)
python -m llmwiki.cli sync

# Force full sync
python -m llmwiki.cli sync --force

# Compile only (no fetch)
python -m llmwiki.cli compile
```

### Query Commands

```bash
# Basic query
python -m llmwiki.cli query "your question"

# Save result as wiki page
python -m llmwiki.cli query "your question" --save

# Limit results
python -m llmwiki.cli query "your question" --top-k 10
```

### Status

```bash
# Show wiki statistics
python -m llmwiki.cli status
```

## Integration with DataSource

### Scenario-Based Usage

**Fast Retrieval** → Use DataSource:
```python
from datasource import DataSourceManager

manager = DataSourceManager()
results = await manager.query("recent bugs", sources=["jira"])
```

**Concept Exploration** → Use LLM Wiki:
```python
from llmwiki import retrieve_from_wiki

results = retrieve_from_wiki(
    query="architectural patterns",
    wiki_dir="llmwiki/wiki"
)
```

### Convenience Scripts

Sync both systems:
```bash
./scripts/sync_all.sh
```

Schedule with cron:
```cron
# DataSource: hourly
0 * * * * cd /path/to/datasource && python -m datasource.cli sync

# LLM Wiki: daily at 2 AM
0 2 * * * cd /path/to/llmwiki && python -m llmwiki.cli sync
```

## Configuration

### config.yaml

```yaml
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
  provider: anthropic  # or "openai"
  model: claude-sonnet-4
  api_key: ${ANTHROPIC_API_KEY}

paths:
  sources: llmwiki/sources
  wiki: llmwiki/wiki
```

### Environment Variables

- `JIRA_API_TOKEN`: Jira API token
- `CONFLUENCE_API_TOKEN`: Confluence API token
- `ANTHROPIC_API_KEY`: Anthropic API key (if using Claude)
- `OPENAI_API_KEY`: OpenAI API key (if using GPT)

## Output Structure

```
llmwiki/
├── sources/              # Markdown sources for compilation
│   ├── jira-PROJ-123.md
│   ├── jira-PROJ-124.md
│   ├── confluence-12345.md
│   └── .content_hashes.json  # Hash tracking
├── wiki/                 # Compiled wiki
│   ├── concepts/         # Concept pages
│   │   ├── Authentication.md
│   │   ├── API_Design.md
│   │   └── ...
│   ├── queries/          # Saved queries
│   └── index.md          # Auto-generated index
├── config.yaml           # Configuration
└── .state.yaml           # Sync state
```

## Comparison: DataSource vs LLM Wiki

| Feature | DataSource | LLM Wiki |
|---------|-----------|----------|
| **Purpose** | Fast retrieval | Concept exploration |
| **Retrieval** | Vector similarity | Vector + BM25 + Graph |
| **Output** | Document chunks | Concept pages |
| **Relationships** | None | Wikilinks |
| **Accumulation** | No | Yes (saved queries) |
| **Update Frequency** | Real-time | Periodic |
| **Best For** | "Find X" | "Understand X" |

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Converters

1. Create `converters/your_source.py`
2. Inherit from `BaseConverter`
3. Implement `convert()` method
4. Register in `converters/__init__.py`

## Troubleshooting

### Sync Issues

```bash
# Check configuration
python -m llmwiki.cli status

# Force full resync
python -m llmwiki.cli sync --force

# Check logs
tail -f llmwiki.log
```

### Compilation Issues

```bash
# Verify llm-wiki-compiler is installed
npx llm-wiki-compiler --version

# Check API keys
echo $ANTHROPIC_API_KEY

# Manual compilation
cd llmwiki
npx llm-wiki-compiler compile
```

## See Also

- [DESIGN.md](DESIGN.md) - Detailed architecture design
- [llm-wiki-compiler](https://github.com/atomicmemory/llm-wiki-compiler) - Core compilation engine
- [DataSource README](../datasource/README.md) - Vector search system
