# 导入未来版本注解
from __future__ import annotations

# 导入日志模块
import logging

# 导入文档切片模型
from app.models.schemas import DocumentChunk
# 导入 DashScope 客户端和错误类
from app.services.dashscope_client import DashScopeClient, DashScopeClientError
# 导入向量存储服务
from app.services.vector_store import VectorStore

# 创建日志记录器
logger = logging.getLogger(__name__)


# RAG（检索增强生成）服务类：核心业务逻辑
# 负责：1）从向量库检索相关文档；2）让 AI 基于文档生成答案
class RagService:
    def __init__(self, vector_store: VectorStore, dashscope_client: DashScopeClient) -> None:
        # 保存向量存储依赖（用于相似度搜索）
        self.vector_store = vector_store
        # 保存 DashScope 客户端依赖（用于调用 AI 模型）
        self.dashscope_client = dashscope_client

    # 问答方法：RAG 的核心入口
    # question: 用户问题；top_k: 检索的文档数量，默认 4 个
    def ask(self, question: str, top_k: int = 4) -> str:
        # 第一步：检索（Retrieval）- 在向量数据库中搜索相似文档
        documents = self.vector_store.similarity_search(question, top_k)
        # 如果没有找到相关文档
        if not documents:
            return "知识库中暂无相关文档，无法基于上下文回答该问题。"
        # 第二步：生成（Generation）- 基于检索到的文档让 AI 生成答案
        return self._generate_answer(question, documents)

    # 生成答案的私有方法：构建提示词并调用 AI 模型
    # question: 用户问题；documents: 检索到的文档列表
    def _generate_answer(self, question: str, documents: list[DocumentChunk]) -> str:
        # 构建上下文：将所有文档片段拼接成一个字符串
        context = "\n\n".join(
            [
                f"[片段 {index + 1}] 来源：{item.metadata.get('source', 'unknown')}\n{item.content}"
                for index, item in enumerate(documents)
            ]
        )
            
        # 系统提示词：指导 AI 如何回答问题
        system_prompt = (
            "你是一个专业的企业知识库问答助手。请根据提供的上下文信息回答用户问题。\n"
            "回答要求：\n"
            "1. 严格基于上下文作答\n"  # 避免 AI 编造答案
            "2. 如果上下文没有答案，请明确说明\n"  # 诚实原则
            "3. 回答准确、简洁、有条理\n"  # 质量要求
            "4. 如果涉及代码，请使用代码块格式"  # 格式要求
        )
            
        # 构建用户提示词：包含上下文和问题
        prompt = f"上下文信息如下：\n{context}\n\n用户问题：{question}"
        try:
            # 调用 DashScope API 生成答案
            return self.dashscope_client.chat(prompt=prompt, system_prompt=system_prompt)
        except DashScopeClientError as exc:
            # 如果 AI 服务不可用，记录警告日志并使用降级方案
            logger.warning("Falling back to extractive answer: %s", exc)
            return self._fallback_answer(question, documents)

    # 静态方法：降级方案的答案生成
    # 当 DashScope 不可用时，直接返回检索到的文档摘要
    @staticmethod
    def _fallback_answer(question: str, documents: list[DocumentChunk]) -> str:
        # 构建文档摘要：每个文档取前 280 个字符
        summary = "\n\n".join(
            [f"- 来源 {item.metadata.get('source', 'unknown')}: {item.content[:280]}" for item in documents]
        )
        # 返回提示信息和摘要
        return (
            "DashScope 当前不可用，下面返回检索到的上下文摘要供参考。\n\n"
            f"问题：{question}\n\n"
            f"相关内容：\n{summary}"
        )
