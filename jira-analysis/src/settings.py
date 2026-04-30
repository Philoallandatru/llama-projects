"""项目配置管理

使用 pydantic-settings 管理配置。
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """项目配置"""

    # Jira 配置
    jira_server: str
    jira_email: str
    jira_token: str

    # LLM 配置
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:14b"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    # 索引路径
    index_base_path: str = "../datasource/data/indexes"

    # Profiles 配置
    profiles_dir: str = "./src/profiles"

    # 批量分析配置
    batch_max_concurrent: int = 5

    # 检索配置
    retrieve_similar_issues_top_k: int = 5
    retrieve_confluence_top_k: int = 3
    retrieve_spec_top_k: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def jira_index_path(self) -> Path:
        """Jira 索引路径"""
        return Path(self.index_base_path) / "jira"

    @property
    def confluence_index_path(self) -> Path:
        """Confluence 索引路径"""
        return Path(self.index_base_path) / "confluence"

    @property
    def spec_index_path(self) -> Path:
        """规格文档索引路径"""
        return Path(self.index_base_path) / "specs"

    def get_jira_config(self) -> dict:
        """获取 Jira 配置"""
        return {
            "server": self.jira_server,
            "email": self.jira_email,
            "token": self.jira_token
        }

    def get_llm_config(self) -> dict:
        """获取 LLM 配置"""
        return {
            "base_url": self.llm_base_url,
            "model": self.llm_model,
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens
        }


# 全局配置实例
settings = Settings()
