"""Incremental sync orchestrator for LLM Wiki layer."""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from llmwiki.config import LLMWikiConfig
from llmwiki.converters.jira import JiraConverter
from llmwiki.converters.confluence import ConfluenceConverter

# Import DataSource clients (reuse existing code)
import sys
sys.path.append(str(Path(__file__).parent.parent / "datasource"))

from datasource.core.sources.jira import JiraDataSource
from datasource.core.sources.confluence import ConfluenceDataSource

logger = logging.getLogger(__name__)


@dataclass
class SyncStats:
    """Statistics for a sync operation."""
    updated: int = 0
    unchanged: int = 0


class WikiSyncOrchestrator:
    """Orchestrates incremental sync from Jira/Confluence to llm-wiki-compiler sources."""

    def __init__(self, config: LLMWikiConfig):
        """
        Initialize sync orchestrator.

        Args:
            config: LLM Wiki configuration
        """
        self.config = config

        # Initialize data sources (reuse DataSource clients)
        self.jira_source = JiraDataSource(
            url=config.jira_url,
            username=config.jira_username,
            api_token=config.jira_api_token,
        )

        self.confluence_source = ConfluenceDataSource(
            url=config.confluence_url,
            username=config.confluence_username,
            api_token=config.confluence_api_token,
        )

        # Initialize converters
        self.jira_converter = JiraConverter(
            jira_url=config.jira_url,
            include_comments=config.include_comments,
            max_comments=config.max_comments,
        )

        self.confluence_converter = ConfluenceConverter(
            confluence_url=config.confluence_url,
            include_comments=config.include_comments,
            max_comments=config.max_comments,
        )

        # Ensure directories exist
        self.sources_dir = config.sources_dir
        self.sources_dir.mkdir(parents=True, exist_ok=True)

        # Hash tracking for incremental updates
        self.hash_file = self.sources_dir / ".content_hashes.json"
        self.hashes = self._load_hashes()

    def sync_all(self, force: bool = False) -> dict[str, int]:
        """
        Sync all data sources incrementally.

        Args:
            force: Force full sync ignoring timestamps

        Returns:
            Dictionary with sync statistics
        """
        logger.info("Starting incremental sync...")

        # Determine sync timestamp
        if force or not self.config.last_sync_timestamp:
            since = None
            logger.info("Performing full sync")
        else:
            since = self.config.last_sync_timestamp
            logger.info(f"Performing incremental sync since {since}")

        # Sync Jira and Confluence concurrently
        jira_stats, confluence_stats = asyncio.run(self._sync_concurrent(since))

        # Update last sync timestamp
        self.config.last_sync_timestamp = datetime.now(timezone.utc)
        self.config.save_state()

        # Save hash tracking
        self._save_hashes()

        stats = {
            "jira_updated": jira_stats.updated,
            "jira_unchanged": jira_stats.unchanged,
            "confluence_updated": confluence_stats.updated,
            "confluence_unchanged": confluence_stats.unchanged,
        }

        logger.info(f"Sync complete: {stats}")
        return stats

    async def _sync_concurrent(self, since: Optional[datetime]) -> tuple[SyncStats, SyncStats]:
        """
        Sync Jira and Confluence concurrently.

        Args:
            since: Only fetch items updated after this timestamp

        Returns:
            Tuple of (jira_stats, confluence_stats)
        """
        jira_task = asyncio.to_thread(self._sync_jira, since)
        confluence_task = asyncio.to_thread(self._sync_confluence, since)
        return await asyncio.gather(jira_task, confluence_task)

    def _sync_jira(self, since: Optional[datetime]) -> SyncStats:
        """
        Sync Jira issues incrementally.

        Args:
            since: Only fetch issues updated after this timestamp

        Returns:
            Statistics dataclass
        """
        stats = SyncStats()

        # Build JQL query for incremental sync
        if since:
            since_str = since.strftime("%Y-%m-%d %H:%M")
            jql = f"updated >= '{since_str}' ORDER BY updated ASC"
        else:
            jql = "ORDER BY updated ASC"

        logger.info(f"Fetching Jira issues with JQL: {jql}")

        # Fetch issues (reuse DataSource client)
        issues = self.jira_source.search_issues(jql=jql, max_results=1000)

        for issue in issues:
            key = issue.get("key", "unknown")
            file_path = self.sources_dir / f"jira-{key}.md"

            # Compute hash of raw API response BEFORE conversion
            raw_hash = self._compute_hash(json.dumps(issue, sort_keys=True))
            previous_hash = self.hashes.get(str(file_path))

            if raw_hash != previous_hash:
                # Content changed, convert and write
                markdown = self.jira_converter.convert(issue)
                file_path.write_text(markdown, encoding="utf-8")
                self.hashes[str(file_path)] = raw_hash
                stats.updated += 1
                logger.debug(f"Updated {file_path}")
            else:
                stats.unchanged += 1
                logger.debug(f"Unchanged {file_path}")

        return stats

    def _sync_confluence(self, since: Optional[datetime]) -> SyncStats:
        """
        Sync Confluence pages incrementally.

        Args:
            since: Only fetch pages updated after this timestamp

        Returns:
            Statistics dataclass
        """
        stats = SyncStats()

        # Fetch pages (reuse DataSource client)
        if since:
            # Confluence API uses ISO format
            since_str = since.isoformat()
            pages = self.confluence_source.get_pages_updated_since(since_str, limit=1000)
        else:
            pages = self.confluence_source.get_all_pages(limit=1000)

        for page in pages:
            page_id = page.get("id", "unknown")
            file_path = self.sources_dir / f"confluence-{page_id}.md"

            # Compute hash of raw API response BEFORE conversion
            raw_hash = self._compute_hash(json.dumps(page, sort_keys=True))
            previous_hash = self.hashes.get(str(file_path))

            if raw_hash != previous_hash:
                # Content changed, convert and write
                markdown = self.confluence_converter.convert(page)
                file_path.write_text(markdown, encoding="utf-8")
                self.hashes[str(file_path)] = raw_hash
                stats.updated += 1
                logger.debug(f"Updated {file_path}")
            else:
                stats.unchanged += 1
                logger.debug(f"Unchanged {file_path}")

        return stats

    def _compute_hash(self, content: str) -> str:
        """
        Compute SHA-256 hash of content.

        Args:
            content: String content

        Returns:
            Hex digest of SHA-256 hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _load_hashes(self) -> dict[str, str]:
        """Load content hashes from tracking file."""
        if not self.hash_file.exists():
            return {}

        with open(self.hash_file) as f:
            return json.load(f)

    def _save_hashes(self):
        """Save content hashes to tracking file."""
        with open(self.hash_file, "w") as f:
            json.dump(self.hashes, f, indent=2)
