#!/usr/bin/env python3
"""Test that all imports work correctly."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test all module imports."""
    print("Testing imports...")

    # Core modules
    from llmwiki import LLMWikiConfig, WikiSyncOrchestrator
    print("[OK] Core modules: LLMWikiConfig, WikiSyncOrchestrator")

    # Retrieval modules
    from llmwiki import WikiRetrieval, QueryResult, query_wiki
    print("[OK] Retrieval modules: WikiRetrieval, QueryResult, query_wiki")

    # Converters
    from llmwiki.converters import JiraConverter, ConfluenceConverter
    print("[OK] Converters: JiraConverter, ConfluenceConverter")

    # CLI utilities
    from llmwiki.cli_utils import print_debug_info
    print("[OK] CLI utilities: print_debug_info")

    print("\n[SUCCESS] All imports successful!")

if __name__ == "__main__":
    test_imports()
