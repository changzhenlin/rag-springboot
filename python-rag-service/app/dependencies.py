# 导入未来版本注解
from __future__ import annotations

# 从 functools 导入 lru_cache，用于实现单例模式（类似 Spring 的 @Scope("singleton")）
from functools import lru_cache

# 导入配置获取函数
from app.core.config import get_settings
# 导入各个服务类（类似 Spring 的 @Service/@Component）
from app.services.dashscope_client import DashScopeClient
from app.services.document_parser import DocumentParserService
from app.services.rag_service import RagService
from app.services.vector_store import VectorStore, build_vector_store


# 使用 LRU 缓存实现单例模式（maxsize=1 表示只缓存一个实例）
# 类似 Spring 的默认单例 Bean，整个应用生命周期内只有一个实例
@lru_cache(maxsize=1)
def get_dashscope_client() -> DashScopeClient:
    # 创建并返回 DashScope 客户端实例（调用阿里云通义千问 API）
    return DashScopeClient(get_settings())


# 文档解析服务的单例工厂方法
@lru_cache(maxsize=1)
def get_document_parser_service() -> DocumentParserService:
    # 创建并返回文档解析器服务实例（负责解析 PDF/Word/Excel 等文件）
    return DocumentParserService(get_settings())


# 向量存储服务的单例工厂方法
@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    # 构建并返回向量存储服务（支持 Milvus 或本地 JSON 存储）
    # 依赖 DashScope 客户端来生成向量嵌入
    return build_vector_store(get_settings(), get_dashscope_client())


# RAG 核心服务的单例工厂方法
@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    # 创建并返回 RAG 服务实例（负责检索 + 生成答案）
    # 依赖向量存储和 DashScope 客户端
    return RagService(get_vector_store(), get_dashscope_client())
