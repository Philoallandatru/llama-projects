"""CLI tool for Jira issue analysis."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from llama_index.core.workflow import draw_all_possible_flows

from .settings import init_settings
from .workflows.deep_analysis import DeepAnalysisWorkflow
from .workflows.batch_analysis import BatchAnalysisWorkflow


@click.group()
def cli():
    """Jira Analysis CLI - Deep analysis of Jira issues using LLM."""
    init_settings()


@cli.command()
@click.argument("issue_key")
@click.option("--mode", type=click.Choice(["fast", "balanced", "thorough"]), default="balanced", help="Analysis mode")
@click.option("--output", "-o", type=click.Path(), help="Output file path (default: stdout)")
@click.option("--format", type=click.Choice(["markdown", "json"]), default="markdown", help="Output format")
def analyze(issue_key: str, mode: str, output: Optional[str], format: str):
    """Analyze a single Jira issue.

    Example:
        jira-analysis analyze PROJ-123 --mode thorough --output report.md
    """
    async def run():
        workflow = DeepAnalysisWorkflow(timeout=300)

        click.echo(f"Analyzing issue {issue_key} in {mode} mode...")

        result = await workflow.run(
            issue_key=issue_key,
            analysis_mode=mode
        )

        if format == "json":
            output_text = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            output_text = result.get("formatted_output", str(result))

        if output:
            Path(output).write_text(output_text, encoding="utf-8")
            click.echo(f"Analysis saved to {output}")
        else:
            click.echo("\n" + output_text)

    asyncio.run(run())


@cli.command()
@click.argument("issue_keys", nargs=-1, required=True)
@click.option("--mode", type=click.Choice(["fast", "balanced", "thorough"]), default="balanced", help="Analysis mode")
@click.option("--output", "-o", type=click.Path(), help="Output directory (default: ./reports)")
@click.option("--summary", is_flag=True, help="Generate summary report")
def batch(issue_keys: tuple, mode: str, output: Optional[str], summary: bool):
    """Analyze multiple Jira issues in parallel.

    Example:
        jira-analysis batch PROJ-123 PROJ-124 PROJ-125 --summary --output ./reports
    """
    async def run():
        workflow = BatchAnalysisWorkflow(timeout=600)

        click.echo(f"Analyzing {len(issue_keys)} issues in {mode} mode...")

        result = await workflow.run(
            issue_keys=list(issue_keys),
            analysis_mode=mode,
            generate_summary=summary
        )

        output_dir = Path(output) if output else Path("./reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save individual reports
        for issue_key, analysis in result.get("analyses", {}).items():
            report_path = output_dir / f"{issue_key}.md"
            report_path.write_text(analysis.get("formatted_output", ""), encoding="utf-8")
            click.echo(f"  {issue_key} -> {report_path}")

        # Save summary if requested
        if summary and "summary" in result:
            summary_path = output_dir / "summary.md"
            summary_path.write_text(result["summary"], encoding="utf-8")
            click.echo(f"  Summary -> {summary_path}")

        click.echo(f"\nCompleted {len(result.get('analyses', {}))} analyses")

    asyncio.run(run())


@cli.command()
@click.option("--workflow", type=click.Choice(["deep", "batch"]), default="deep", help="Workflow to visualize")
@click.option("--output", "-o", type=click.Path(), default="workflow.html", help="Output HTML file")
def visualize(workflow: str, output: str):
    """Visualize workflow structure.

    Example:
        jira-analysis visualize --workflow deep --output deep_workflow.html
    """
    if workflow == "deep":
        wf = DeepAnalysisWorkflow()
    else:
        wf = BatchAnalysisWorkflow()

    draw_all_possible_flows(wf, filename=output)
    click.echo(f"Workflow visualization saved to {output}")


@cli.command()
def profiles():
    """List available analysis profiles."""
    config_path = Path(__file__).parent / "profiles" / "config.json"

    with open(config_path) as f:
        config = json.load(f)

    click.echo("Available Analysis Profiles:\n")

    for profile_name, profile_config in config["profiles"].items():
        click.echo(f"  {profile_name}:")
        click.echo(f"    Description: {profile_config.get('description', 'N/A')}")
        click.echo(f"    Issue Types: {', '.join(profile_config.get('issue_types', []))}")
        click.echo(f"    Retrieval: top_k={profile_config.get('retrieval', {}).get('top_k', 'N/A')}")
        click.echo()


@cli.command()
@click.option("--check-llm", is_flag=True, help="Check LLM connection")
@click.option("--check-jira", is_flag=True, help="Check Jira connection")
@click.option("--check-index", is_flag=True, help="Check vector index")
def doctor(check_llm: bool, check_jira: bool, check_index: bool):
    """Run diagnostic checks.

    Example:
        jira-analysis doctor --check-llm --check-jira
    """
    import os
    from llama_index.llms.ollama import Ollama

    all_checks = not (check_llm or check_jira or check_index)

    if all_checks or check_llm:
        click.echo("Checking LLM connection...")
        try:
            llm = Ollama(
                model=os.getenv("MODEL", "llama3.2"),
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            )
            response = llm.complete("Hello")
            click.echo(f"  ✓ LLM is accessible (model: {os.getenv('MODEL', 'llama3.2')})")
        except Exception as e:
            click.echo(f"  ✗ LLM connection failed: {e}")

    if all_checks or check_jira:
        click.echo("Checking Jira connection...")
        jira_url = os.getenv("JIRA_URL")
        jira_token = os.getenv("JIRA_TOKEN")

        if not jira_url or not jira_token:
            click.echo("  ✗ JIRA_URL or JIRA_TOKEN not set in environment")
        else:
            try:
                import requests
                response = requests.get(
                    f"{jira_url}/rest/api/2/serverInfo",
                    headers={"Authorization": f"Bearer {jira_token}"},
                    timeout=10
                )
                if response.status_code == 200:
                    click.echo(f"  ✓ Jira is accessible ({jira_url})")
                else:
                    click.echo(f"  ✗ Jira returned status {response.status_code}")
            except Exception as e:
                click.echo(f"  ✗ Jira connection failed: {e}")

    if all_checks or check_index:
        click.echo("Checking vector indices...")
        confluence_index = Path(os.getenv("CONFLUENCE_INDEX_PATH", "./data/confluence_index"))
        spec_index = Path(os.getenv("SPEC_INDEX_PATH", "./data/spec_index"))

        if confluence_index.exists():
            click.echo(f"  ✓ Confluence index found at {confluence_index}")
        else:
            click.echo(f"  ✗ Confluence index not found at {confluence_index}")

        if spec_index.exists():
            click.echo(f"  ✓ Spec index found at {spec_index}")
        else:
            click.echo(f"  ✗ Spec index not found at {spec_index}")


if __name__ == "__main__":
    cli()
