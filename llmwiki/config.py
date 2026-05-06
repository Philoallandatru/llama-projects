"""Configuration management for LLM Wiki layer."""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class LLMWikiConfig:
    """Configuration for LLM Wiki layer."""

    # Jira connection
    jira_url: str
    jira_username: str
    jira_api_token: str

    # Confluence connection
    confluence_url: str
    confluence_username: str
    confluence_api_token: str

    # Sync settings
    sync_interval_hours: int = 24
    last_sync_timestamp: Optional[datetime] = None

    # llm-wiki-compiler settings
    sources_dir: Path = field(default_factory=lambda: Path("llmwiki/sources"))
    wiki_dir: Path = field(default_factory=lambda: Path("llmwiki/wiki"))
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4"
    llm_api_key: str = ""
    llm_base_url: str = ""  # For LM Studio or custom OpenAI-compatible endpoints

    # Conversion settings
    include_comments: bool = True
    include_attachments: bool = False
    max_description_length: int = 5000
    max_comments: int = 10

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "LLMWikiConfig":
        """
        Load configuration from YAML file with environment variable substitution.

        Args:
            config_path: Path to config file (default: auto-detect)

        Returns:
            LLMWikiConfig instance
        """
        if config_path is None:
            # Try multiple locations
            candidates = [
                Path("config.yaml"),           # Current directory
                Path("llmwiki/config.yaml"),   # From project root
            ]

            for candidate in candidates:
                if candidate.exists():
                    config_path = candidate
                    break

            if config_path is None:
                raise FileNotFoundError(
                    f"Config file not found. Tried: {', '.join(str(c) for c in candidates)}"
                )

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Substitute environment variables
        config_dict = {
            "jira_url": data["jira"]["url"],
            "jira_username": data["jira"]["username"],
            "jira_api_token": cls._resolve_env(data["jira"]["api_token"]),
            "confluence_url": data["confluence"]["url"],
            "confluence_username": data["confluence"]["username"],
            "confluence_api_token": cls._resolve_env(data["confluence"]["api_token"]),
            "sync_interval_hours": data.get("sync", {}).get("interval_hours", 24),
            "include_comments": data.get("sync", {}).get("include_comments", True),
            "include_attachments": data.get("sync", {}).get("include_attachments", False),
            "llm_provider": data.get("llm", {}).get("provider", "anthropic"),
            "llm_model": data.get("llm", {}).get("model", "claude-sonnet-4"),
            "llm_api_key": cls._resolve_env(data.get("llm", {}).get("api_key", "")),
            "llm_base_url": data.get("llm", {}).get("base_url", ""),
            "sources_dir": Path(data.get("paths", {}).get("sources", "llmwiki/sources")),
            "wiki_dir": Path(data.get("paths", {}).get("wiki", "llmwiki/wiki")),
        }

        # Load last sync timestamp from state file if exists
        state_file = Path("llmwiki/.state.yaml")
        if state_file.exists():
            with open(state_file) as f:
                state = yaml.safe_load(f)
                if last_sync := state.get("last_sync_timestamp"):
                    config_dict["last_sync_timestamp"] = datetime.fromisoformat(last_sync)

        return cls(**config_dict)

    def save_state(self):
        """Save sync state to file."""
        state_file = Path("llmwiki/.state.yaml")
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "last_sync_timestamp": self.last_sync_timestamp.isoformat() if self.last_sync_timestamp else None
        }

        with open(state_file, "w") as f:
            yaml.dump(state, f)

    @staticmethod
    def _resolve_env(value: str) -> str:
        """Resolve environment variable references like ${VAR_NAME}."""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.environ.get(env_var, "")
        return value

    def validate(self) -> list[str]:
        """
        Validate configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.jira_url:
            errors.append("jira_url is required")
        if not self.jira_username:
            errors.append("jira_username is required")
        if not self.jira_api_token:
            errors.append("jira_api_token is required (check JIRA_API_TOKEN env var)")

        if not self.confluence_url:
            errors.append("confluence_url is required")
        if not self.confluence_username:
            errors.append("confluence_username is required")
        if not self.confluence_api_token:
            errors.append("confluence_api_token is required (check CONFLUENCE_API_TOKEN env var)")

        if not self.llm_api_key:
            errors.append("llm_api_key is required (check ANTHROPIC_API_KEY or OPENAI_API_KEY env var)")

        if self.llm_provider not in ["anthropic", "openai"]:
            errors.append(f"llm_provider must be 'anthropic' or 'openai', got '{self.llm_provider}'")

        return errors
