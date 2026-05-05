"""Confluence page to Markdown converter."""

import sys
from pathlib import Path
from typing import Any, Optional

from llmwiki.converters.base import BaseConverter

# Import HTMLCleaner from datasource
sys.path.append(str(Path(__file__).parent.parent.parent / "datasource"))
from datasource.core.utils.html_cleaner import HTMLCleaner


class ConfluenceConverter(BaseConverter):
    """Converts Confluence pages to narrative Markdown suitable for concept extraction."""

    def __init__(self, confluence_url: str, include_comments: bool = True, max_comments: int = 10):
        """
        Initialize Confluence converter.

        Args:
            confluence_url: Base URL of Confluence instance
            include_comments: Whether to include comments in output
            max_comments: Maximum number of comments to include
        """
        self.confluence_url = confluence_url.rstrip("/")
        self.include_comments = include_comments
        self.max_comments = max_comments
        self.html_cleaner = HTMLCleaner()

    def convert(self, page: dict[str, Any]) -> str:
        """
        Convert Confluence page JSON to narrative Markdown.

        Args:
            page: Confluence page JSON from API

        Returns:
            Human-readable Markdown suitable for concept extraction
        """
        page_id = page.get("id", "unknown")
        title = page.get("title", "Untitled")

        # Build metadata frontmatter
        metadata = self._build_metadata(page, page_id)

        # Build narrative content
        content_parts = [
            self._format_metadata(metadata),
            self._build_header(title),
            self._build_overview(page),
            self._build_body(page),
            self._build_children(page),
            self._build_attachments(page),
            self._build_comments(page),
        ]

        # Filter out empty sections
        content = "\n".join(part for part in content_parts if part.strip())

        return content

    def _build_metadata(self, page: dict[str, Any], page_id: str) -> dict[str, Any]:
        """Build frontmatter metadata."""
        space = page.get("space", {})
        version = page.get("version", {})

        return {
            "source": "confluence",
            "page_id": page_id,
            "space": space.get("key", ""),
            "space_name": space.get("name", ""),
            "type": page.get("type", "page"),
            "status": page.get("status", "current"),
            "version": version.get("number", 1),
            "created": page.get("history", {}).get("createdDate", ""),
            "updated": version.get("when", ""),
            "url": f"{self.confluence_url}/pages/viewpage.action?pageId={page_id}",
        }

    def _build_header(self, title: str) -> str:
        """Build the main header."""
        return f"# {title}\n"

    def _build_overview(self, page: dict[str, Any]) -> str:
        """Build the overview section with key metadata."""
        lines = ["## Overview\n"]

        page_type = page.get("type", "page")
        status = page.get("status", "current")
        lines.append(f"This is a Confluence **{page_type}** with status **{status}**.")

        # Add space context
        space = page.get("space", {})
        if space_name := space.get("name"):
            space_key = space.get("key", "")
            lines.append(f"**Space:** {space_name} ({space_key})")

        # Add author information
        history = page.get("history", {})
        if creator := history.get("createdBy"):
            lines.append(f"**Created by:** {creator.get('displayName', 'Unknown')}")

        version = page.get("version", {})
        if author := version.get("by"):
            lines.append(f"**Last modified by:** {author.get('displayName', 'Unknown')}")

        # Add labels
        if metadata := page.get("metadata"):
            if labels := metadata.get("labels", {}).get("results", []):
                tags = ", ".join(f"#{label.get('name', '')}" for label in labels)
                lines.append(f"**Labels:** {tags}")

        return "\n".join(lines) + "\n"

    def _build_body(self, page: dict[str, Any]) -> str:
        """Build the main content section."""
        body = page.get("body", {})

        # Try storage format first (most complete)
        if storage := body.get("storage"):
            content = storage.get("value", "")
            return self._convert_storage_format(content) + "\n"

        # Fallback to view format
        if view := body.get("view"):
            content = view.get("value", "")
            return self._convert_html_to_markdown(content) + "\n"

        return ""

    def _build_children(self, page: dict[str, Any]) -> str:
        """Build child pages section."""
        children = page.get("children", {})
        child_pages = children.get("page", {}).get("results", [])

        if not child_pages:
            return ""

        lines = ["## Child Pages\n"]

        for child in child_pages:
            child_id = child.get("id", "")
            child_title = child.get("title", "Untitled")
            lines.append(f"- [[confluence-{child_id}|{child_title}]]")

        return "\n".join(lines) + "\n"

    def _build_attachments(self, page: dict[str, Any]) -> str:
        """Build attachments section."""
        children = page.get("children", {})
        attachments = children.get("attachment", {}).get("results", [])

        if not attachments:
            return ""

        lines = ["## Attachments\n"]

        for attachment in attachments:
            title = attachment.get("title", "Untitled")
            media_type = attachment.get("metadata", {}).get("mediaType", "")
            lines.append(f"- {title} ({media_type})")

        return "\n".join(lines) + "\n"

    def _build_comments(self, page: dict[str, Any]) -> str:
        """Build comments section."""
        if not self.include_comments:
            return ""

        children = page.get("children", {})
        comments = children.get("comment", {}).get("results", [])

        if not comments:
            return ""

        lines = ["## Comments\n"]

        # Limit to most recent comments
        recent_comments = comments[-self.max_comments:]

        for comment in recent_comments:
            version = comment.get("version", {})
            author = version.get("by", {}).get("displayName", "Unknown")
            when = version.get("when", "")

            lines.append(f"**{author}** commented on {when}:\n")

            body = comment.get("body", {})
            if storage := body.get("storage"):
                content = storage.get("value", "")
                lines.append(self._convert_storage_format(content))
            elif view := body.get("view"):
                content = view.get("value", "")
                lines.append(self._convert_html_to_markdown(content))

            lines.append("\n---\n")

        return "\n".join(lines)

    def _convert_storage_format(self, content: str) -> str:
        """
        Convert Confluence storage format (XHTML) to Markdown.

        Args:
            content: XHTML content from storage format

        Returns:
            Markdown string
        """
        # Use existing HTMLCleaner utility from datasource
        return self.html_cleaner.clean(content)

    def _convert_html_to_markdown(self, html: str) -> str:
        """
        Convert HTML to Markdown.

        Args:
            html: HTML content

        Returns:
            Markdown string
        """
        return self.html_cleaner.clean(html)
