import os

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI


def init_settings():
    # 支持本地 LM Studio 或 OpenAI
    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

    if use_local:
        # 使用本地 LM Studio
        base_url = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
        model = os.getenv("LM_STUDIO_MODEL", "local-model")
        timeout = float(os.getenv("REQUEST_TIMEOUT", "300"))

        Settings.llm = OpenAI(
            model=model,
            api_base=base_url,
            api_key="dummy",  # LM Studio 不需要真实的 API key
            timeout=timeout
        )

        # 本地 embedding 模型（如果有的话）
        embed_base_url = os.getenv("LM_STUDIO_EMBED_BASE_URL", base_url)
        embed_model = os.getenv("LM_STUDIO_EMBED_MODEL", "text-embedding-3-large")
        Settings.embed_model = OpenAIEmbedding(
            model=embed_model,
            api_base=embed_base_url,
            api_key="dummy",
            timeout=timeout
        )
    else:
        # 使用 OpenAI
        if os.getenv("OPENAI_API_KEY") is None:
            raise RuntimeError("OPENAI_API_KEY is missing in environment variables")
        Settings.llm = OpenAI(model=os.getenv("MODEL") or "gpt-4.1")
        Settings.embed_model = OpenAIEmbedding(
            model=os.getenv("EMBEDDING_MODEL") or "text-embedding-3-large"
        )
