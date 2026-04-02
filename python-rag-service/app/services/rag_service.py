from __future__ import annotations

import logging

from app.models.schemas import DocumentChunk
from app.services.dashscope_client import DashScopeClient, DashScopeClientError
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RagService:
    def __init__(self, vector_store: VectorStore, dashscope_client: DashScopeClient) -> None:
        self.vector_store = vector_store
        self.dashscope_client = dashscope_client

    def ask(self, question: str, top_k: int = 4) -> str:
        documents = self.vector_store.similarity_search(question, top_k)
        if not documents:
            return "知识库中暂无相关文档，无法基于上下文回答该问题。"
        return self._generate_answer(question, documents)

    def _generate_answer(self, question: str, documents: list[DocumentChunk]) -> str:
        context = "\n\n".join(
            [
                f"[片段 {index + 1}] 来源: {item.metadata.get('source', 'unknown')}\n{item.content}"
                for index, item in enumerate(documents)
            ]
        )
        system_prompt = (
            "你是一个专业的企业知识库问答助手。请根据提供的上下文信息回答用户问题。\n"
            "回答要求：\n"
            "1. 严格基于上下文作答\n"
            "2. 如果上下文没有答案，请明确说明\n"
            "3. 回答准确、简洁、有条理\n"
            "4. 如果涉及代码，请使用代码块格式"
        )
        prompt = f"上下文信息如下：\n{context}\n\n用户问题：{question}"
        try:
            return self.dashscope_client.chat(prompt=prompt, system_prompt=system_prompt)
        except DashScopeClientError as exc:
            logger.warning("Falling back to extractive answer: %s", exc)
            return self._fallback_answer(question, documents)

    @staticmethod
    def _fallback_answer(question: str, documents: list[DocumentChunk]) -> str:
        summary = "\n\n".join(
            [f"- 来源 {item.metadata.get('source', 'unknown')}: {item.content[:280]}" for item in documents]
        )
        return (
            "DashScope 当前不可用，下面返回检索到的上下文摘要供参考。\n\n"
            f"问题：{question}\n\n"
            f"相关内容：\n{summary}"
        )
