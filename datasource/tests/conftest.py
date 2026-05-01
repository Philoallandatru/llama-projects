"""测试配置 - 使用 mock 嵌入模型"""

import pytest
from llama_index.core import Settings
from llama_index.core.embeddings import MockEmbedding


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """设置测试环境 - 使用 mock 嵌入模型"""
    # 使用 mock 嵌入模型避免需要 API 密钥
    Settings.embed_model = MockEmbedding(embed_dim=384)
    Settings.llm = None  # 不需要 LLM

    yield

    # 清理
    Settings.embed_model = None
