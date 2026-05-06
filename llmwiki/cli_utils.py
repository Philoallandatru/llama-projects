"""Helper functions for CLI output formatting."""


def print_debug_info(debug):
    """Print retrieval debug information."""
    import click

    click.echo("\n🔍 Retrieval Debug Info\n")

    # Retrieval method
    method = "chunk-level" if debug.used_chunks else "page-level"
    reranked = "yes" if debug.reranked else "no"
    click.echo(f"Method: {method}, Reranked: {reranked}\n")

    # Page scores
    click.echo("📄 Selected Pages:")
    for page in debug.pages:
        slug = page["slug"]
        score = page["score"]
        click.echo(f"  • {slug} (best chunk score: {score:.3f})")

    # Chunk details
    if debug.chunks:
        click.echo(f"\n📝 Top Chunks ({len(debug.chunks)} total):")
        for chunk in debug.chunks[:10]:  # Show top 10
            preview = chunk.text[:80].replace("\n", " ").strip()
            click.echo(
                f"  · {chunk.slug}#{chunk.chunk_index} "
                f"(score: {chunk.score:.3f})\n"
                f"    {preview}..."
            )
