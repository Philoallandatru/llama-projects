#!/usr/bin/env python3
"""Test WikiRetrieval Node.js bridge."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llmwiki import WikiRetrieval

def test_retrieval():
    """Test retrieval functionality."""
    print("Testing WikiRetrieval...")

    # Initialize retrieval
    wiki_dir = Path("wiki")
    if not wiki_dir.exists():
        print(f"[SKIP] Wiki directory not found: {wiki_dir}")
        print("Run 'llmwiki sync' first to create the wiki.")
        return

    retrieval = WikiRetrieval(wiki_dir=wiki_dir)
    print(f"[OK] WikiRetrieval initialized with wiki_dir={wiki_dir}")

    # Test query
    query = "What is the project structure?"
    print(f"\n[TEST] Querying: {query}")

    try:
        result = retrieval.query(query, top_k=5, rerank_keep=3, debug=True)
        print(f"\n[OK] Query successful!")
        print(f"Answer: {result.answer[:200]}...")
        print(f"Chunks: {len(result.chunks)}")
        print(f"Pages: {len(result.pages)}")
        if result.reasoning:
            print(f"Reasoning: {result.reasoning[:200]}...")
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()
