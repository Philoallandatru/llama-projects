"""Jira issue to Markdown converter."""

import re
from typing import Any, Optional

from llmwiki.converters.base import BaseConverter


class JiraConverter(BaseConverter):
    """Converts Jira issues to narrative Markdown suitable for concept extraction."""

    def __init__(self, jira_url: str, include_comments: bool = True, max_comments: int = 10):
        """
        Initialize Jira converter.

        Args:
            jira_url: Base URL of Jira instance
            include_comments: Whether to include comments in output
            max_comments: Maximum number of comments to include
        """
        self.jira_url = jira_url.rstrip("/")
        self.include_comments = include_comments
        self.max_comments = max_comments

    def convert(self, issue: dict[str, Any]) -> str:
        """
        Convert Jira issue JSON to narrative Markdown.

        Args:
            issue: Jira issue JSON from API

        Returns:
            Human-readable Markdown suitable for concept extraction
        """
        fields = issue.get("fields", {})
        key = issue.get("key", "UNKNOWN")

        # Build metadata frontmatter
        metadata = self._build_metadata(issue, fields, key)

        # Build narrative content
        content_parts = [
            self._format_metadata(metadata),
            self._build_header(key, fields),
            self._build_overview(fields),
            self._build_description(fields),
            self._build_acceptance_criteria(fields),
            self._build_relationships(fields),
            self._build_links(fields),
            self._build_comments(fields),
        ]

        # Filter out empty sections
        content = "\n".join(part for part in content_parts if part.strip())

        return content

    def _build_metadata(self, issue: dict[str, Any], fields: dict[str, Any], key: str) -> dict[str, Any]:
        """Build frontmatter metadata."""
        return {
            "source": "jira",
            "key": key,
            "type": fields.get("issuetype", {}).get("name", "Unknown"),
            "status": fields.get("status", {}).get("name", "Unknown"),
            "priority": fields.get("priority", {}).get("name", "Unknown"),
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
            "url": f"{self.jira_url}/browse/{key}",
        }

    def _build_header(self, key: str, fields: dict[str, Any]) -> str:
        """Build the main header."""
        summary = fields.get("summary", "Untitled")
        return f"# {key}: {summary}\n"

    def _build_overview(self, fields: dict[str, Any]) -> str:
        """Build the overview section with key metadata."""
        issue_type = fields.get("issuetype", {}).get("name", "issue")
        status = fields.get("status", {}).get("name", "unknown status")
        priority = fields.get("priority", {}).get("name", "")

        lines = [
            "## Overview\n",
            f"This is a **{issue_type}** currently in **{status}** status.",
        ]

        if priority:
            lines.append(f"Priority: **{priority}**")

        # Add people
        if assignee := fields.get("assignee"):
            lines.append(f"**Assigned to:** {assignee.get('displayName', 'Unknown')}")

        if reporter := fields.get("reporter"):
            lines.append(f"**Reported by:** {reporter.get('displayName', 'Unknown')}")

        # Add project context
        if project := fields.get("project"):
            lines.append(f"**Project:** {project.get('name', 'Unknown')}")

        # Add labels/tags
        if labels := fields.get("labels"):
            tags = ", ".join(f"#{label}" for label in labels)
            lines.append(f"**Tags:** {tags}")

        return "\n".join(lines) + "\n"

    def _build_description(self, fields: dict[str, Any]) -> str:
        """Build the description section."""
        description = fields.get("description")
        if not description:
            return ""

        lines = ["## Description\n"]

        # Convert ADF or plain text to Markdown
        if isinstance(description, dict):
            md_description = self._convert_adf_to_markdown(description)
        else:
            md_description = str(description)

        lines.append(md_description)
        return "\n".join(lines) + "\n"

    def _build_acceptance_criteria(self, fields: dict[str, Any]) -> str:
        """Build acceptance criteria section if present."""
        # Check common custom field names for acceptance criteria
        ac_field_names = [
            "customfield_10100",  # Common AC field
            "acceptance_criteria",
            "acceptanceCriteria",
        ]

        for field_name in ac_field_names:
            if ac := fields.get(field_name):
                lines = ["## Acceptance Criteria\n"]
                if isinstance(ac, dict):
                    lines.append(self._convert_adf_to_markdown(ac))
                else:
                    lines.append(str(ac))
                return "\n".join(lines) + "\n"

        return ""

    def _build_relationships(self, fields: dict[str, Any]) -> str:
        """Build relationships section (parent, subtasks, epic)."""
        lines = []

        # Parent issue
        if parent := fields.get("parent"):
            lines.append(f"**Parent Issue:** [[{parent.get('key')}]] - {parent.get('fields', {}).get('summary', '')}")

        # Epic link
        if epic_key := fields.get("customfield_10014"):  # Common epic link field
            lines.append(f"**Epic:** [[{epic_key}]]")

        # Subtasks
        if subtasks := fields.get("subtasks"):
            lines.append("\n**Subtasks:**")
            for subtask in subtasks:
                key = subtask.get("key", "")
                summary = subtask.get("fields", {}).get("summary", "")
                status = subtask.get("fields", {}).get("status", {}).get("name", "")
                lines.append(f"- [[{key}]] - {summary} ({status})")

        if lines:
            return "## Relationships\n\n" + "\n".join(lines) + "\n"
        return ""

    def _build_links(self, fields: dict[str, Any]) -> str:
        """Build issue links section."""
        issuelinks = fields.get("issuelinks", [])
        if not issuelinks:
            return ""

        lines = ["## Related Issues\n"]

        for link in issuelinks:
            link_type = link.get("type", {})

            if "outwardIssue" in link:
                related = link["outwardIssue"]
                relationship = link_type.get("outward", "relates to")
                key = related.get("key", "")
                summary = related.get("fields", {}).get("summary", "")
                lines.append(f"- **{relationship}:** [[{key}]] - {summary}")

            elif "inwardIssue" in link:
                related = link["inwardIssue"]
                relationship = link_type.get("inward", "relates to")
                key = related.get("key", "")
                summary = related.get("fields", {}).get("summary", "")
                lines.append(f"- **{relationship}:** [[{key}]] - {summary}")

        return "\n".join(lines) + "\n"

    def _build_comments(self, fields: dict[str, Any]) -> str:
        """Build comments section."""
        if not self.include_comments:
            return ""

        comments = fields.get("comment", {}).get("comments", [])
        if not comments:
            return ""

        lines = ["## Discussion\n"]

        # Limit to most recent comments
        recent_comments = comments[-self.max_comments:]

        for comment in recent_comments:
            author = comment.get("author", {}).get("displayName", "Unknown")
            created = comment.get("created", "")
            body = comment.get("body", "")

            lines.append(f"**{author}** commented on {created}:\n")

            if isinstance(body, dict):
                lines.append(self._convert_adf_to_markdown(body))
            else:
                lines.append(str(body))

            lines.append("\n---\n")

        return "\n".join(lines)

    def _convert_adf_to_markdown(self, adf: dict[str, Any]) -> str:
        """
        Convert Atlassian Document Format to Markdown.

        Args:
            adf: ADF JSON structure

        Returns:
            Markdown string
        """
        if isinstance(adf, str):
            return adf

        if not isinstance(adf, dict):
            return str(adf)

        # Handle top-level doc
        if adf.get("type") == "doc":
            content_nodes = adf.get("content", [])
            return "\n\n".join(self._convert_adf_node(node) for node in content_nodes)

        return self._convert_adf_node(adf)

    def _convert_adf_node(self, node: dict[str, Any]) -> str:
        """Convert a single ADF node to Markdown."""
        node_type = node.get("type", "")

        if node_type == "paragraph":
            return self._convert_paragraph(node)
        elif node_type == "heading":
            return self._convert_heading(node)
        elif node_type == "bulletList":
            return self._convert_bullet_list(node)
        elif node_type == "orderedList":
            return self._convert_ordered_list(node)
        elif node_type == "listItem":
            return self._convert_list_item(node)
        elif node_type == "codeBlock":
            return self._convert_code_block(node)
        elif node_type == "blockquote":
            return self._convert_blockquote(node)
        elif node_type == "panel":
            return self._convert_panel(node)
        elif node_type == "table":
            return self._convert_table(node)
        elif node_type == "text":
            return self._convert_text(node)

        # Fallback: try to process content
        if "content" in node:
            return "".join(self._convert_adf_node(child) for child in node["content"])

        return ""

    def _convert_paragraph(self, node: dict[str, Any]) -> str:
        """Convert paragraph node."""
        content = node.get("content", [])
        return "".join(self._convert_adf_node(child) for child in content)

    def _convert_heading(self, node: dict[str, Any]) -> str:
        """Convert heading node."""
        level = node.get("attrs", {}).get("level", 1)
        content = node.get("content", [])
        text = "".join(self._convert_adf_node(child) for child in content)
        return f"{'#' * level} {text}"

    def _convert_bullet_list(self, node: dict[str, Any]) -> str:
        """Convert bullet list node."""
        items = node.get("content", [])
        return "\n".join(f"- {self._convert_adf_node(item)}" for item in items)

    def _convert_ordered_list(self, node: dict[str, Any]) -> str:
        """Convert ordered list node."""
        items = node.get("content", [])
        return "\n".join(f"{i+1}. {self._convert_adf_node(item)}" for i, item in enumerate(items))

    def _convert_list_item(self, node: dict[str, Any]) -> str:
        """Convert list item node."""
        content = node.get("content", [])
        return "".join(self._convert_adf_node(child) for child in content)

    def _convert_code_block(self, node: dict[str, Any]) -> str:
        """Convert code block node."""
        content = node.get("content", [])
        code = "".join(child.get("text", "") for child in content)
        lang = node.get("attrs", {}).get("language", "")
        return f"```{lang}\n{code}\n```"

    def _convert_blockquote(self, node: dict[str, Any]) -> str:
        """Convert blockquote node."""
        content = node.get("content", [])
        lines = "\n\n".join(self._convert_adf_node(child) for child in content)
        return "\n".join(f"> {line}" for line in lines.split("\n"))

    def _convert_panel(self, node: dict[str, Any]) -> str:
        """Convert panel node (info/warning/error boxes)."""
        panel_type = node.get("attrs", {}).get("panelType", "info")
        content = node.get("content", [])
        text = "\n\n".join(self._convert_adf_node(child) for child in content)
        return f"**{panel_type.upper()}:**\n{text}"

    def _convert_table(self, node: dict[str, Any]) -> str:
        """Convert table node (simplified)."""
        # Full table conversion is complex, simplified version
        return "[Table content - see original issue for details]"

    def _convert_text(self, node: dict[str, Any]) -> str:
        """Convert text node with marks (bold, italic, etc.)."""
        text = node.get("text", "")
        marks = node.get("marks", [])

        for mark in marks:
            mark_type = mark.get("type", "")
            if mark_type == "strong":
                text = f"**{text}**"
            elif mark_type == "em":
                text = f"*{text}*"
            elif mark_type == "code":
                text = f"`{text}`"
            elif mark_type == "link":
                href = mark.get("attrs", {}).get("href", "")
                text = f"[{text}]({href})"
            elif mark_type == "strike":
                text = f"~~{text}~~"

        return text
