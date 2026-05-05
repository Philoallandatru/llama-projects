"""项目配置管理

支持从 config.yaml 或 .env 文件加载配置。
优先级：config.yaml > .env > 默认值
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_yaml_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """从 YAML 文件加载配置"""
    # Try to find config.yaml in multiple locations
    search_paths = [
        Path(config_path),  # Current directory
        Path(__file__).parent.parent / config_path,  # jira-analysis root
        Path(__file__).parent.parent.parent / config_path,  # llama-projects root
    ]

    path = None
    for p in search_paths:
        if p.exists():
            path = p
            break

    if path is None:
        return {}

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # 将嵌套的 YAML 结构展平为环境变量格式
    flat_config = {}

    # Jira 配置
    if jira := config.get("jira"):
        flat_config["jira_server"] = jira.get("server")
        flat_config["jira_email"] = jira.get("email")
        flat_config["jira_token"] = jira.get("token")

    # LLM 配置
    if llm := config.get("llm"):
        flat_config["llm_base_url"] = llm.get("base_url")
        flat_config["llm_model"] = llm.get("model")
        flat_config["llm_temperature"] = llm.get("temperature")
        flat_config["llm_max_tokens"] = llm.get("max_tokens")
        flat_config["llm_api_key"] = llm.get("api_key")

    # 索引配置
    if index := config.get("index"):
        flat_config["index_base_path"] = index.get("base_path")

    # 工作流配置
    if workflow := config.get("workflow"):
        if deep := workflow.get("deep_analysis"):
            flat_config["retrieve_similar_issues_top_k"] = deep.get("max_evidence_items", 10)
        if batch := workflow.get("batch_analysis"):
            flat_config["batch_max_concurrent"] = batch.get("max_concurrent", 5)

    # 本地测试配置
    if local_test := config.get("local_test"):
        flat_config["local_test_enabled"] = local_test.get("enabled", False)
        flat_config["use_mock_data"] = local_test.get("use_mock_data", False)
        flat_config["mock_data_path"] = local_test.get("mock_data_path")

    return {k: v for k, v in flat_config.items() if v is not None}


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
    llm_api_key: str = "ollama"

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

    # 本地测试配置
    local_test_enabled: bool = False
    use_mock_data: bool = False
    mock_data_path: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
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
            "max_tokens": self.llm_max_tokens,
            "api_key": self.llm_api_key
        }


# 加载 YAML 配置（如果存在）
_yaml_config = load_yaml_config()

# 全局配置实例（YAML 配置会覆盖默认值）
settings = Settings(**_yaml_config)


def init_settings():
    """初始化 LlamaIndex Settings（LLM 和 Embedding）

    这个函数用于在应用启动时配置全局的 LLM 和 Embedding 模型。
    """
    from llama_index.core import Settings as LlamaSettings
    from llama_index.llms.openai import OpenAI
    from llama_index.embeddings.openai import OpenAIEmbedding

    # 配置 LLM
    LlamaSettings.llm = OpenAI(
        model="gpt-3.5-turbo",  # 使用已知模型名称通过验证
        api_base=settings.llm_base_url,
        api_key=settings.llm_api_key,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=300
    )

    # 配置 Embedding
    LlamaSettings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_base=settings.llm_base_url,
        api_key=settings.llm_api_key,
        timeout=300
    )
