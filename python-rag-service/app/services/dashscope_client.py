# 导入未来版本注解
from __future__ import annotations

# 导入 hashlib 用于生成本地向量（类似 Java 的 MessageDigest）
import hashlib
# 导入日志模块
import logging
# 导入 math 用于数学计算
import math
# 导入类型提示
from typing import Iterable

# 导入配置类
from app.core.config import Settings

# 创建日志记录器
logger = logging.getLogger(__name__)

# 尝试导入 dashscope SDK（阿里云通义千问的 Python 客户端）
try:
    import dashscope
    from dashscope import Generation, TextEmbedding
except ImportError:  # pragma: no cover
    # 如果未安装，则设置为 None，避免导入失败
    dashscope = None
    Generation = None
    TextEmbedding = None


# 自定义异常类：DashScope 客户端错误（类似 Java 的自定义 Exception）
class DashScopeClientError(Exception):
    pass


# DashScope 客户端类：负责调用阿里云百炼平台的 API
# 类似 Spring 中调用外部 REST API 的服务类
class DashScopeClient:
    def __init__(self, settings: Settings) -> None:
        # 保存配置对象
        self.settings = settings
        # 如果 dashscope 已安装，则设置 API Key
        if dashscope is not None:
            dashscope.api_key = settings.dashscope_api_key

    # 检查是否已配置（类似 Spring 的 Environment 检查属性是否存在）
    def is_configured(self) -> bool:
        # 返回 API Key 是否存在且 dashscope 库已安装
        return bool(self.settings.dashscope_api_key and dashscope is not None)

    # 文本嵌入方法：将文本列表转换为向量（用于语义搜索）
    # 输入：文本迭代器；输出：二维向量列表
    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        # 将迭代器转换为列表
        texts = list(texts)
        if not texts:
            return []
        # 如果已配置，则调用 DashScope API
        if self.is_configured():
            return self._embed_with_dashscope(texts)
        # 否则使用本地降级方案（生成确定性向量）
        logger.warning("DashScope embedding unavailable, using deterministic local embedding fallback")
        return [self._fallback_embedding(text) for text in texts]

    # 聊天方法：调用大模型进行对话
    # prompt: 用户问题；system_prompt: 系统提示词（可选）
    def chat(self, prompt: str, system_prompt: str | None = None) -> str:
        # 检查是否已配置
        if not self.is_configured():
            raise DashScopeClientError("DashScope 未配置，请设置 DASHSCOPE_API_KEY")
        assert Generation is not None
            
        # 构建消息列表
        messages = []
        # 如果有系统提示词，添加到消息列表
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        # 添加用户消息
        messages.append({"role": "user", "content": prompt})
            
        # 调用 DashScope API
        response = Generation.call(
            model=self.settings.dashscope_chat_model,  # 使用的模型名称
            messages=messages,  # 对话历史
            temperature=self.settings.dashscope_temperature,  # 温度参数
            result_format="message",  # 返回格式
        )
            
        # 检查响应状态码
        if response.status_code != 200:
            raise DashScopeClientError(
                f"DashScope 调用失败：{response.code or response.status_code} {response.message}"
            )
        # 返回 AI 生成的回答内容
        return response.output["choices"][0]["message"]["content"]

    # 使用 DashScope API 生成向量嵌入的私有方法
    def _embed_with_dashscope(self, texts: list[str]) -> list[list[float]]:
        assert TextEmbedding is not None
        vectors: list[list[float]] = []
        # 遍历每个文本，调用嵌入 API
        for text in texts:
            response = TextEmbedding.call(
                model=self.settings.dashscope_embedding_model,
                input=text,
            )
            # 检查响应状态
            if response.status_code != 200:
                raise DashScopeClientError(
                    f"DashScope embedding 调用失败：{response.code or response.status_code} {response.message}"
                )
            # 提取向量数据并转换为 float 列表
            embedding = response.output["embeddings"][0]["embedding"]
            vectors.append([float(item) for item in embedding])
        return vectors

    # 降级的向量化方法：当 DashScope 不可用时使用 SHA256 哈希生成确定性向量
    # 这种方法不能捕捉语义相似性，但可以作为临时方案
    def _fallback_embedding(self, text: str) -> list[float]:
        # 获取配置的向量维度
        dimension = self.settings.milvus_dimension
        # 初始化零向量
        vector = [0.0] * dimension
        # 将文本转为小写并分词
        tokens = text.lower().split()
        if not tokens:
            return vector
        # 对每个 token 计算 SHA256 哈希
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            # 将哈希字节映射到向量元素
            for index in range(0, min(len(digest), dimension)):
                vector[index] += digest[index] / 255.0
        # 归一化向量（L2 归一化）
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
