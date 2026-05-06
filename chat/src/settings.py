import os
from pathlib import Path
import yaml

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        raise RuntimeError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def init_settings():
    """初始化 LLM 和 Embedding 设置"""
    config = load_config()
    llm_config = config.get('llm', {})

    base_url = llm_config.get('base_url', 'http://localhost:11434/v1')
    model = llm_config.get('model', 'qwen2.5:14b')
    api_key = llm_config.get('api_key', 'ollama')
    temperature = llm_config.get('temperature', 0.1)
    max_tokens = llm_config.get('max_tokens', 4096)

    # 配置 LLM
    # 使用已知模型名称通过验证，实际请求会发送到 LM Studio
    Settings.llm = OpenAI(
        model="gpt-3.5-turbo",  # 使用已知模型名称通过验证
        api_base=base_url,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=300
    )

    # 配置 Embedding（使用 LM Studio 中的 embedding 模型）
    # 使用已知模型名称通过验证，实际请求会发送到 LM Studio
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_base=base_url,
        api_key=api_key,
        timeout=300
    )
