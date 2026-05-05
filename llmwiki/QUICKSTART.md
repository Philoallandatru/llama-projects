# LLM Wiki Layer - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Python dependencies
pip install pyyaml click

# Node.js dependencies (for llm-wiki-compiler)
npm install -g llm-wiki-compiler
```

### 2. Initialize Project

```bash
cd llama-projects
python -m llmwiki init
```

This creates:
```
llmwiki/
├── config.yaml          # Configuration file
├── sources/             # Markdown sources (auto-generated)
└── wiki/                # Compiled wiki (auto-generated)
```

### 3. Configure

Edit `llmwiki/config.yaml`:

```yaml
jira:
  url: https://your-domain.atlassian.net
  username: your-email@example.com
  api_token: ${JIRA_API_TOKEN}

confluence:
  url: https://your-domain.atlassian.net/wiki
  username: your-email@example.com
  api_token: ${CONFLUENCE_API_TOKEN}

llm:
  provider: anthropic
  model: claude-sonnet-4
  api_key: ${ANTHROPIC_API_KEY}
```

Set environment variables:
```bash
export JIRA_API_TOKEN="your-jira-token"
export CONFLUENCE_API_TOKEN="your-confluence-token"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### 4. Sync Data

```bash
# First sync (full)
python -m llmwiki sync

# Subsequent syncs (incremental)
python -m llmwiki sync
```

Output:
```
🔄 Starting sync...

✅ Sync complete!
  Jira: 150 updated, 0 unchanged
  Confluence: 45 updated, 0 unchanged

📚 Compiling wiki...
✅ Compilation complete!
```

### 5. Query

```bash
# Basic query
python -m llmwiki query "What is the authentication flow?"

# Advanced query with debug info
python -m llmwiki query "What are the main architectural patterns?" \
    --debug \
    --top-k 30 \
    --rerank-keep 10

# Save query result as wiki page
python -m llmwiki query "What is our deployment process?" --save
```

Output:
```
🔍 Question: What is the authentication flow?

📄 Selecting relevant pages...

💡 Reasoning: Selected 3 page(s) from 15 reranked chunks
📚 Selected pages: auth-patterns, api-security, oauth-flow

✨ Answer:

The authentication flow consists of three main steps:
1. User submits credentials to /auth/login endpoint
2. Server validates credentials and generates JWT token
3. Client includes token in Authorization header for subsequent requests

The system supports both session-based and token-based authentication...
```

## 📊 Check Status

```bash
python -m llmwiki status
```

Output:
```
📊 Wiki Status

Sources:
  Jira: 150 issues
  Confluence: 45 pages

Wiki:
  Concepts: 87 pages

Last sync: 2026-05-05 00:45:23
```

## 🔍 Retrieval Features

### Chunk-Level Retrieval
- Retrieves at paragraph level (not page level)
- More precise context selection
- Better for large documents

### BM25 Reranking
- Combines semantic (embeddings) + lexical (BM25) signals
- Improves keyword-heavy queries
- Reduces false positives

### Parameters
- `--top-k`: Initial chunks to retrieve (default: 20)
- `--rerank-keep`: Chunks to keep after BM25 (default: 5)
- `--debug`: Show retrieval debug info
- `--save`: Save answer as wiki page

## 🎯 Use Cases

### 1. Onboarding
```bash
python -m llmwiki query "What are the main components of the system?" --save
python -m llmwiki query "How do I set up my development environment?" --save
```

### 2. Architecture Review
```bash
python -m llmwiki query "What are the authentication patterns?" --debug
python -m llmwiki query "How does the API gateway work?" --debug
```

### 3. Troubleshooting
```bash
python -m llmwiki query "How do I debug authentication failures?"
python -m llmwiki query "What are common deployment issues?"
```

## 🔄 Incremental Sync

The system uses two-level incremental detection:

1. **Timestamp-based** (fast): Only fetch items updated since last sync
2. **Hash-based** (accurate): SHA-256 hash detects actual content changes

```bash
# Incremental (default)
python -m llmwiki sync

# Force full sync
python -m llmwiki sync --force
```

## 🐍 Python API

```python
from llmwiki import query_wiki, LLMWikiConfig

# Load config
config = LLMWikiConfig.load()

# Query
result = query_wiki(
    config=config,
    question="What is authentication?",
    save=True,
    debug=True,
    top_k=20,
    rerank_keep=5
)

# Access results
print(f"Answer: {result.answer}")
print(f"Pages: {result.selected_pages}")
print(f"Reasoning: {result.reasoning}")

if result.debug:
    for chunk in result.debug.chunks:
        print(f"  {chunk.slug}#{chunk.chunk_index}: {chunk.score:.3f}")
```

## 📚 Documentation

- `README.md` - Full user guide
- `DESIGN.md` - Architecture and design decisions
- `DEEP_RETRIEVAL.md` - Retrieval pipeline details
- `STATUS.md` - Project status and deliverables
- `SUMMARY.md` - Implementation summary

## 🆘 Troubleshooting

### "No module named llmwiki"
```bash
# Make sure you're in the project root
cd llama-projects
python -m llmwiki --help
```

### "llm-wiki-compiler not found"
```bash
# Install globally
npm install -g llm-wiki-compiler

# Or use npx (auto-downloads)
# The system uses npx by default
```

### "Configuration errors"
```bash
# Check config file
cat llmwiki/config.yaml

# Validate environment variables
echo $JIRA_API_TOKEN
echo $ANTHROPIC_API_KEY
```

### "Wiki directory not found"
```bash
# Run sync first
python -m llmwiki sync
```

## 🎉 Next Steps

1. ✅ Sync your first data sources
2. ✅ Try a few queries
3. ✅ Explore debug mode
4. ✅ Save useful queries as wiki pages
5. ✅ Set up automated sync (cron/scheduler)

---

**Need help?** Check the full documentation in `README.md` or `DESIGN.md`.
