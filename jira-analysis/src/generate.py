"""
Index generation script for Confluence and specification documents.
"""
import asyncio
import os
from pathlib import Path
from typing import List

import click
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.vector_stores import SimpleVectorStore

from src.settings import init_settings


class IndexGenerator:
    """Generate and persist vector indexes for retrieval."""

    def __init__(self, persist_dir: str = "data/indexes"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

    def generate_from_directory(
        self,
        source_dir: str,
        index_name: str,
        file_extractor: dict = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> VectorStoreIndex:
        """Generate index from a directory of documents."""
        print(f"Loading documents from {source_dir}...")

        reader = SimpleDirectoryReader(
            input_dir=source_dir,
            recursive=True,
            file_extractor=file_extractor,
        )
        documents = reader.load_data()
        print(f"Loaded {len(documents)} documents")

        print("Parsing documents into nodes...")
        parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        nodes = parser.get_nodes_from_documents(documents)
        print(f"Created {len(nodes)} nodes")

        print("Building vector index...")
        index = VectorStoreIndex(nodes, show_progress=True)

        print(f"Persisting index to {self.persist_dir / index_name}...")
        index.storage_context.persist(persist_dir=str(self.persist_dir / index_name))

        print(f"✓ Index '{index_name}' generated successfully")
        return index

    def load_index(self, index_name: str) -> VectorStoreIndex:
        """Load a persisted index."""
        index_path = self.persist_dir / index_name
        if not index_path.exists():
            raise FileNotFoundError(f"Index not found: {index_path}")

        storage_context = StorageContext.from_defaults(
            docstore=SimpleDocumentStore.from_persist_dir(persist_dir=str(index_path)),
            vector_store=SimpleVectorStore.from_persist_dir(persist_dir=str(index_path)),
            index_store=SimpleIndexStore.from_persist_dir(persist_dir=str(index_path)),
        )

        return VectorStoreIndex.from_storage_context(storage_context)

    def update_index(
        self,
        index_name: str,
        new_documents_dir: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> VectorStoreIndex:
        """Incrementally update an existing index with new documents."""
        print(f"Loading existing index '{index_name}'...")
        index = self.load_index(index_name)

        print(f"Loading new documents from {new_documents_dir}...")
        reader = SimpleDirectoryReader(
            input_dir=new_documents_dir,
            recursive=True,
        )
        documents = reader.load_data()
        print(f"Loaded {len(documents)} new documents")

        print("Parsing new documents...")
        parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        nodes = parser.get_nodes_from_documents(documents)
        print(f"Created {len(nodes)} new nodes")

        print("Updating index...")
        index.insert_nodes(nodes)

        print(f"Persisting updated index...")
        index.storage_context.persist(persist_dir=str(self.persist_dir / index_name))

        print(f"✓ Index '{index_name}' updated successfully")
        return index


@click.group()
def cli():
    """Index generation CLI."""
    load_dotenv()
    init_settings()


@cli.command()
@click.option("--confluence-dir", required=True, help="Directory containing Confluence exports")
@click.option("--spec-dir", required=True, help="Directory containing specification documents")
@click.option("--persist-dir", default="data/indexes", help="Directory to persist indexes")
@click.option("--chunk-size", default=512, help="Chunk size for text splitting")
@click.option("--chunk-overlap", default=50, help="Chunk overlap for text splitting")
def generate(confluence_dir: str, spec_dir: str, persist_dir: str, chunk_size: int, chunk_overlap: int):
    """Generate both Confluence and specification indexes."""
    generator = IndexGenerator(persist_dir=persist_dir)

    print("\n=== Generating Confluence Index ===")
    generator.generate_from_directory(
        source_dir=confluence_dir,
        index_name="confluence",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    print("\n=== Generating Specification Index ===")
    generator.generate_from_directory(
        source_dir=spec_dir,
        index_name="specifications",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    print("\n✓ All indexes generated successfully!")


@cli.command()
@click.option("--index-name", required=True, help="Name of the index to update")
@click.option("--new-docs-dir", required=True, help="Directory containing new documents")
@click.option("--persist-dir", default="data/indexes", help="Directory where indexes are persisted")
@click.option("--chunk-size", default=512, help="Chunk size for text splitting")
@click.option("--chunk-overlap", default=50, help="Chunk overlap for text splitting")
def update(index_name: str, new_docs_dir: str, persist_dir: str, chunk_size: int, chunk_overlap: int):
    """Incrementally update an existing index with new documents."""
    generator = IndexGenerator(persist_dir=persist_dir)

    generator.update_index(
        index_name=index_name,
        new_documents_dir=new_docs_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


@cli.command()
@click.option("--index-name", required=True, help="Name of the index to query")
@click.option("--query", required=True, help="Query string")
@click.option("--top-k", default=5, help="Number of results to return")
@click.option("--persist-dir", default="data/indexes", help="Directory where indexes are persisted")
def query(index_name: str, query: str, top_k: int, persist_dir: str):
    """Test query an index."""
    generator = IndexGenerator(persist_dir=persist_dir)

    print(f"Loading index '{index_name}'...")
    index = generator.load_index(index_name)

    print(f"\nQuerying: {query}")
    print(f"Top {top_k} results:\n")

    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)

    for i, node in enumerate(nodes, 1):
        print(f"--- Result {i} (score: {node.score:.4f}) ---")
        print(node.text[:300] + "..." if len(node.text) > 300 else node.text)
        print()


if __name__ == "__main__":
    cli()
