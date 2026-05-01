"""LLM 客户端

封装本地 LLM 调用，支持流式输出。
"""

import logging
from typing import AsyncIterator, Dict, Any

from llama_index.llms.openai_like import OpenAILike

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端

    职责：
    - 封装本地 LLM 调用（Ollama/LM Studio）
    - 支持流式和非流式输出
    - 处理错误和重试
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化 LLM 客户端

        Args:
            config: LLM 配置，包含：
                - base_url: API 基础 URL（如 "http://localhost:11434/v1"）
                - model: 模型名称（如 "qwen2.5:14b"）
                - temperature: 温度参数（默认 0.1）
                - max_tokens: 最大 token 数（默认 4096）
        """
        self.config = config
        self.base_url = config["base_url"]
        self.model = config["model"]
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 4096)

        # 创建 LLM 实例
        self.llm = OpenAILike(
            api_base=self.base_url,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            is_chat_model=True,
            api_key="dummy"  # 本地模型不需要真实 API key
        )

        logger.info(
            f"LLMClient initialized: base_url={self.base_url}, "
            f"model={self.model}, temperature={self.temperature}"
        )

    async def generate(self, prompt: str) -> str:
        """生成分析报告（非流式）

        Args:
            prompt: 输入 prompt

        Returns:
            生成的文本

        Raises:
            Exception: 生成失败
        """
        try:
            response = await self.llm.acomplete(prompt)
            text = response.text
            logger.info(f"Generated {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Failed to generate: {e}")
            raise

    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """流式生成（用于实时 UI 反馈）

        Args:
            prompt: 输入 prompt

        Yields:
            生成的文本片段

        Raises:
            Exception: 生成失败
        """
        try:
            response = await self.llm.astream_complete(prompt)
            total_chars = 0

            async for chunk in response:
                delta = chunk.delta
                if delta:
                    total_chars += len(delta)
                    yield delta

            logger.info(f"Streamed {total_chars} characters")

        except Exception as e:
            logger.error(f"Failed to stream generate: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息

        Returns:
            模型配置信息
        """
        return {
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
