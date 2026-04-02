from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.dashscope_client import DashScopeClient
from app.services.document_parser import DocumentParserService
from app.services.rag_service import RagService
from app.services.vector_store import VectorStore, build_vector_store


@lru_cache(maxsize=1)
def get_dashscope_client() -> DashScopeClient:
    return DashScopeClient(get_settings())


@lru_cache(maxsize=1)
def get_document_parser_service() -> DocumentParserService:
    return DocumentParserService(get_settings())


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    return build_vector_store(get_settings(), get_dashscope_client())


@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    return RagService(get_vector_store(), get_dashscope_client())
