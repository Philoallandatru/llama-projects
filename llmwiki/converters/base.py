"""Base converter interface for JSON to Markdown conversion."""

from abc import ABC, abstractmethod
from typing import Any


class BaseConverter(ABC):
    """Base class for JSON to Markdown converters."""

    @abstractmethod
    def convert(self, data: dict[str, Any]) -> str:
        """
        Convert structured data to narrative Markdown.

        Args:
            data: Structured data (JSON) from data source

        Returns:
            Human-readable Markdown suitable for concept extraction
        """
        pass

    def _format_metadata(self, metadata: dict[str, Any]) -> str:
        """
        Format metadata as YAML frontmatter.

        Args:
            metadata: Dictionary of metadata key-value pairs

        Returns:
            YAML frontmatter block
        """
        lines = ["---"]
        for key, value in metadata.items():
            # Handle None values
            if value is None:
                value = ""
            # Escape strings with special characters
            if isinstance(value, str) and (":" in value or "\n" in value):
                value = f'"{value}"'
            lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")
        return "\n".join(lines)
