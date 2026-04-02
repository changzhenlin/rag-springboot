from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in (None, "") else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "rag-python-service")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = _env_int("SERVER_PORT", 8080)
    cors_origins: list[str] = None  # type: ignore[assignment]

    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    dashscope_chat_model: str = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-max")
    dashscope_embedding_model: str = os.getenv(
        "DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3"
    )
    dashscope_temperature: float = _env_float("DASHSCOPE_TEMPERATURE", 0.7)

    milvus_host: str = os.getenv("MILVUS_HOST", "localhost")
    milvus_port: int = _env_int("MILVUS_PORT", 19530)
    milvus_username: str = os.getenv("MILVUS_USERNAME", "")
    milvus_password: str = os.getenv("MILVUS_PASSWORD", "")
    milvus_collection_name: str = os.getenv("MILVUS_COLLECTION_NAME", "rag_documents")
    milvus_dimension: int = _env_int("MILVUS_DIMENSION", 1536)
    milvus_index_type: str = os.getenv("MILVUS_INDEX_TYPE", "IVF_FLAT")
    milvus_metric_type: str = os.getenv("MILVUS_METRIC_TYPE", "COSINE")

    vector_backend: str = os.getenv("VECTOR_BACKEND", "auto")
    local_store_path: str = os.getenv(
        "LOCAL_VECTOR_STORE_PATH", "data/local_vector_store.json"
    )

    chunk_size: int = _env_int("CHUNK_SIZE", 1000)
    chunk_overlap: int = _env_int("CHUNK_OVERLAP", 120)

    def __post_init__(self) -> None:
        origins = os.getenv("CORS_ORIGINS", "*")
        object.__setattr__(
            self,
            "cors_origins",
            ["*"] if origins == "*" else [item.strip() for item in origins.split(",") if item.strip()],
        )
        store_path = Path(self.local_store_path)
        if not store_path.is_absolute():
            root = Path(__file__).resolve().parents[2]
            object.__setattr__(self, "local_store_path", str(root / store_path))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
