from __future__ import annotations

import hashlib
import logging
import math
from typing import Iterable

from app.core.config import Settings

logger = logging.getLogger(__name__)

try:
    import dashscope
    from dashscope import Generation, TextEmbedding
except ImportError:  # pragma: no cover
    dashscope = None
    Generation = None
    TextEmbedding = None


class DashScopeClientError(Exception):
    pass


class DashScopeClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if dashscope is not None:
            dashscope.api_key = settings.dashscope_api_key

    def is_configured(self) -> bool:
        return bool(self.settings.dashscope_api_key and dashscope is not None)

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        texts = list(texts)
        if not texts:
            return []
        if self.is_configured():
            return self._embed_with_dashscope(texts)
        logger.warning("DashScope embedding unavailable, using deterministic local embedding fallback")
        return [self._fallback_embedding(text) for text in texts]

    def chat(self, prompt: str, system_prompt: str | None = None) -> str:
        if not self.is_configured():
            raise DashScopeClientError("DashScope 未配置，请设置 DASHSCOPE_API_KEY")
        assert Generation is not None
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = Generation.call(
            model=self.settings.dashscope_chat_model,
            messages=messages,
            temperature=self.settings.dashscope_temperature,
            result_format="message",
        )
        if response.status_code != 200:
            raise DashScopeClientError(
                f"DashScope 调用失败: {response.code or response.status_code} {response.message}"
            )
        return response.output["choices"][0]["message"]["content"]

    def _embed_with_dashscope(self, texts: list[str]) -> list[list[float]]:
        assert TextEmbedding is not None
        vectors: list[list[float]] = []
        for text in texts:
            response = TextEmbedding.call(
                model=self.settings.dashscope_embedding_model,
                input=text,
            )
            if response.status_code != 200:
                raise DashScopeClientError(
                    f"DashScope embedding 调用失败: {response.code or response.status_code} {response.message}"
                )
            embedding = response.output["embeddings"][0]["embedding"]
            vectors.append([float(item) for item in embedding])
        return vectors

    def _fallback_embedding(self, text: str) -> list[float]:
        dimension = self.settings.milvus_dimension
        vector = [0.0] * dimension
        tokens = text.lower().split()
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index in range(0, min(len(digest), dimension)):
                vector[index] += digest[index] / 255.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
