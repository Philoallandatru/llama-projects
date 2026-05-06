#!/bin/bash
# Sync both DataSource and LLM Wiki systems

set -e

echo "🔄 Syncing all knowledge systems..."
echo ""

# Sync DataSource
echo "📦 Syncing DataSource (vector search)..."
cd datasource
python -m datasource.cli sync --incremental
echo "✅ DataSource sync complete"
echo ""

# Sync LLM Wiki
echo "📚 Syncing LLM Wiki (knowledge graph)..."
cd ../llmwiki
python -m llmwiki.cli sync
echo "✅ LLM Wiki sync complete"
echo ""

echo "🎉 All systems synced successfully!"
