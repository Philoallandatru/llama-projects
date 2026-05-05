"""Command-line interface for LLM Wiki."""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path

import click

from llmwiki.config import LLMWikiConfig
from llmwiki.sync import WikiSyncOrchestrator
from llmwiki.cli_utils import print_debug_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.pass_context
def cli(ctx, config):
    """LLM Wiki - Knowledge graph from Jira and Confluence."""
    ctx.ensure_object(dict)

    # Load configuration
    try:
        config_path = Path(config) if config else None
        ctx.obj["config"] = LLMWikiConfig.load(config_path)

        # Validate configuration
        errors = ctx.obj["config"].validate()
        if errors:
            click.echo("Configuration errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nCreate a config file at llmwiki/config.yaml with:", err=True)
        click.echo(_get_config_template(), err=True)
        sys.exit(1)


@cli.command()
@click.option("--force", is_flag=True, help="Force full sync (ignore timestamps)")
@click.pass_context
def sync(ctx, force):
    """Sync data sources and compile wiki."""
    config = ctx.obj["config"]

    click.echo("Starting sync...")

    # Run sync
    orchestrator = WikiSyncOrchestrator(config)
    stats = orchestrator.sync_all(force=force)

    # Display results
    click.echo("\nSync complete!")
    click.echo(f"  Jira: {stats['jira_updated']} updated, {stats['jira_unchanged']} unchanged")
    click.echo(f"  Confluence: {stats['confluence_updated']} updated, {stats['confluence_unchanged']} unchanged")

    # Run compilation
    if stats['jira_updated'] > 0 or stats['confluence_updated'] > 0:
        click.echo("\nCompiling wiki...")
        try:
            _run_llmwiki_compile(config)
            click.echo("Compilation complete!")
        except Exception as e:
            click.echo(f"Compilation failed: {e}", err=True)
            sys.exit(1)
    else:
        click.echo("\nNo changes detected, skipping compilation")


@cli.command()
@click.pass_context
def compile(ctx):
    """Compile wiki from existing sources/ directory."""
    config = ctx.obj["config"]

    click.echo("Compiling wiki...")

    try:
        _run_llmwiki_compile(config)
        click.echo("Compilation complete!")
    except Exception as e:
        click.echo(f"Compilation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("question")
@click.option("--save", is_flag=True, help="Save query result as wiki page")
@click.option("--debug", is_flag=True, help="Show retrieval debug information")
@click.option("--top-k", default=20, help="Number of chunks to retrieve initially")
@click.option("--rerank-keep", default=5, help="Number of chunks to keep after BM25 reranking")
@click.pass_context
def query(ctx, question, save, debug, top_k, rerank_keep):
    """
    Query the compiled wiki using chunk-level retrieval + BM25 reranking.

    This uses llm-wiki-compiler's two-stage retrieval pipeline:
    1. Chunk-level embeddings → BM25 reranking → page selection
    2. Load full pages + chunk excerpts → LLM answer generation
    """
    config = ctx.obj["config"]

    click.echo(f"Question: {question}\n")
    click.echo("Selecting relevant pages...")

    try:
        from llmwiki.retrieval import query_wiki, QueryOptions

        # Query with streaming output
        result = query_wiki(
            config=config,
            question=question,
            options=QueryOptions(
                save=save,
                debug=debug,
                top_k=top_k,
                rerank_keep=rerank_keep,
            ),
        )

        # Display results
        click.echo(f"\nReasoning: {result.reasoning}")
        click.echo(f"Selected pages: {', '.join(result.selected_pages)}\n")

        click.echo("Answer:\n")
        click.echo(result.answer)
        click.echo()

        # Show debug info if requested
        if debug and result.debug:
            print_debug_info(result.debug)

        # Show save confirmation
        if result.saved_slug:
            click.echo(f"Saved as: {result.saved_slug}.md")
            click.echo("   Future queries will use this answer as context.")
        elif not save:
            click.echo("Tip: use --save to add this answer to your wiki")

    except Exception as e:
        click.echo(f"Query failed: {e}", err=True)
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show wiki status and statistics."""
    config = ctx.obj["config"]

    click.echo("Wiki Status\n")

    # Count source files
    sources_dir = config.sources_dir
    if sources_dir.exists():
        jira_count = len(list(sources_dir.glob("jira-*.md")))
        confluence_count = len(list(sources_dir.glob("confluence-*.md")))
        click.echo(f"Sources:")
        click.echo(f"  Jira: {jira_count} issues")
        click.echo(f"  Confluence: {confluence_count} pages")
    else:
        click.echo("Sources: Not initialized")

    # Count wiki pages
    wiki_dir = config.wiki_dir / "concepts"
    if wiki_dir.exists():
        concept_count = len(list(wiki_dir.glob("*.md")))
        click.echo(f"\nWiki:")
        click.echo(f"  Concepts: {concept_count} pages")
    else:
        click.echo("\nWiki: Not compiled yet")

    # Last sync time
    if config.last_sync_timestamp:
        click.echo(f"\nLast sync: {config.last_sync_timestamp}")
    else:
        click.echo("\nLast sync: Never")


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize LLM Wiki directory structure and config."""
    click.echo("Initializing LLM Wiki...\n")

    # Create directories
    dirs = [
        Path("llmwiki"),
        Path("llmwiki/sources"),
        Path("llmwiki/wiki"),
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        click.echo(f"Created {dir_path}/")

    # Create config template
    config_path = Path("llmwiki/config.yaml")
    if config_path.exists():
        click.echo(f"\nConfig file already exists: {config_path}")
    else:
        config_path.write_text(_get_config_template())
        click.echo(f"\nCreated {config_path}")

    click.echo("\nInitialization complete!")
    click.echo("\nNext steps:")
    click.echo("  1. Edit llmwiki/config.yaml with your credentials")
    click.echo("  2. Set environment variables (JIRA_API_TOKEN, etc.)")
    click.echo("  3. Run: llmwiki sync")


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["llms-txt", "llms-full-txt", "json", "json-ld", "graphml", "marp"]),
    default="llms-txt",
    help="Export format",
)
@click.option("--output", "-o", help="Output file path (default: dist/exports/)")
@click.pass_context
def export(ctx, format: str, output: str | None):
    """Export wiki to various formats (llms-txt, JSON, GraphML, etc)."""
    config = ctx.obj["config"]

    click.echo(f"Exporting wiki to {format} format...")

    try:
        _run_llmwiki_export(config, format, output)
        click.echo("Export complete!")

        # Show output location
        if not output:
            export_dir = config.sources_dir.parent / "dist" / "exports"
            if format == "llms-txt":
                output_file = export_dir / "llms.txt"
            elif format == "llms-full-txt":
                output_file = export_dir / "llms-full.txt"
            else:
                output_file = export_dir / f"export.{format}"

            if output_file.exists():
                size = output_file.stat().st_size
                click.echo(f"\n✓ Exported to: {output_file}")
                click.echo(f"  Size: {size:,} bytes")

    except Exception as e:
        click.echo(f"Export failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def lint(ctx):
    """Check wiki quality (broken links, structure issues)."""
    config = ctx.obj["config"]

    click.echo("Checking wiki quality...")

    try:
        _run_llmwiki_lint(config)
    except Exception as e:
        click.echo(f"Lint failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--interval", type=int, default=300, help="Sync interval in seconds (default: 300)")
@click.pass_context
def watch(ctx, interval: int):
    """Watch for changes and auto-sync + compile."""
    import time
    from datetime import datetime

    config = ctx.obj["config"]

    click.echo(f"Starting watch mode (sync interval: {interval}s)")
    click.echo("Press Ctrl+C to stop\n")

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"[{timestamp}] Syncing...")

            try:
                # Sync data sources
                from llmwiki.sync import WikiSyncOrchestrator

                orchestrator = WikiSyncOrchestrator(config)
                stats = orchestrator.sync_all(force=False)

                jira_updated = stats.get("jira_updated", 0)
                confluence_updated = stats.get("confluence_updated", 0)

                if jira_updated > 0 or confluence_updated > 0:
                    click.echo(f"  Jira: {jira_updated} updated, Confluence: {confluence_updated} updated")

                    # Trigger compile
                    click.echo("  Compiling...")
                    _run_llmwiki_compile(config)
                    click.echo("  Compile completed")
                else:
                    click.echo("  No changes detected")

            except Exception as e:
                click.echo(f"  ✗ Error: {e}", err=True)
                if ctx.obj.get("debug"):
                    import traceback
                    traceback.print_exc()

            click.echo(f"  Next sync in {interval}s...\n")
            time.sleep(interval)

    except KeyboardInterrupt:
        click.echo("\n\nWatch mode stopped")



def _run_llmwiki_compile(config: LLMWikiConfig):
    """Run llm-wiki-compiler on sources directory."""
    cmd = [
        "npx",
        "llm-wiki-compiler",
        "compile",
    ]

    # Set environment variables for llm-wiki-compiler
    env = {
        "LLMWIKI_PROVIDER": config.llm_provider,
        "LLMWIKI_MODEL": config.llm_model,
    }

    if config.llm_provider == "anthropic":
        env["ANTHROPIC_API_KEY"] = config.llm_api_key
    elif config.llm_provider == "openai":
        env["OPENAI_API_KEY"] = config.llm_api_key
        if config.llm_base_url:
            env["OPENAI_BASE_URL"] = config.llm_base_url

    # Run from the parent directory of sources/
    cwd = str(config.sources_dir.parent)

    # Don't capture output - let it stream directly to terminal to avoid encoding issues
    result = subprocess.run(
        cmd,
        env={**subprocess.os.environ, **env},
        shell=True,
        cwd=cwd,
    )

    if result.returncode != 0:
        raise RuntimeError(f"llm-wiki-compiler failed with exit code {result.returncode}")


def _run_llmwiki_export(config: LLMWikiConfig, format: str, output: str | None):
    """Run llm-wiki-compiler export command."""
    import os

    cmd = [
        "npx",
        "llm-wiki-compiler",
        "export",
        "--target", format,
    ]

    if output:
        cmd.extend(["--output", output])

    # Use the parent directory of sources as working directory
    cwd = str(config.sources_dir.parent)

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8',  # Fix Windows encoding issues
        shell=True,  # Required on Windows for npx
    )

    if result.returncode != 0:
        raise RuntimeError(f"Export failed: {result.stderr}")

    # Print output
    if result.stdout:
        click.echo(result.stdout)


def _run_llmwiki_lint(config: LLMWikiConfig):
    """Run llm-wiki-compiler lint command."""
    cmd = [
        "npx",
        "llm-wiki-compiler",
        "lint",
    ]

    cwd = str(config.sources_dir.parent)

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8',  # Fix Windows encoding issues
        shell=True,  # Required on Windows for npx
    )

    # Print output (lint may return non-zero if issues found)
    if result.stdout:
        click.echo(result.stdout)
    if result.stderr:
        click.echo(result.stderr, err=True)



def _get_config_template() -> str:
    """Get configuration file template."""
    return """# LLM Wiki Configuration

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
"""


if __name__ == "__main__":
    cli()
