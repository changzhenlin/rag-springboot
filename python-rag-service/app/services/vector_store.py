from __future__ import annotations

import json
import logging
import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.models.schemas import DocumentChunk
from app.services.dashscope_client import DashScopeClient

logger = logging.getLogger(__name__)

try:
    from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility
except ImportError:  # pragma: no cover
    Collection = None
    CollectionSchema = None
    DataType = None
    FieldSchema = None
    connections = None
    utility = None


class VectorStore(ABC):
    backend_name: str = "unknown"

    @abstractmethod
    def add_documents(self, documents: list[DocumentChunk]) -> None:
        raise NotImplementedError

    @abstractmethod
    def similarity_search(self, query: str, top_k: int) -> list[DocumentChunk]:
        raise NotImplementedError

    @abstractmethod
    def delete_documents(self, document_ids: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def has_documents(self) -> bool:
        raise NotImplementedError


class LocalVectorStore(VectorStore):
    backend_name = "local"

    def __init__(self, settings: Settings, dashscope_client: DashScopeClient) -> None:
        self.settings = settings
        self.dashscope_client = dashscope_client
        self.store_path = Path(settings.local_store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self.store_path.write_text("[]", encoding="utf-8")

    def add_documents(self, documents: list[DocumentChunk]) -> None:
        rows = self._load()
        embeddings = self.dashscope_client.embed([item.content for item in documents])
        for item, embedding in zip(documents, embeddings):
            rows.append(
                {
                    "id": item.id,
                    "content": item.content,
                    "metadata": item.metadata,
                    "embedding": embedding,
                }
            )
        self._save(rows)

    def similarity_search(self, query: str, top_k: int) -> list[DocumentChunk]:
        rows = self._load()
        if not rows:
            return []
        [query_embedding] = self.dashscope_client.embed([query])
        ranked = sorted(
            rows,
            key=lambda row: self._cosine_similarity(query_embedding, row["embedding"]),
            reverse=True,
        )[:top_k]
        return [
            DocumentChunk(
                id=row["id"],
                content=row["content"],
                metadata=row.get("metadata", {}),
                score=self._cosine_similarity(query_embedding, row["embedding"]),
            )
            for row in ranked
        ]

    def delete_documents(self, document_ids: list[str]) -> None:
        rows = [row for row in self._load() if row["id"] not in set(document_ids)]
        self._save(rows)

    def has_documents(self) -> bool:
        return bool(self._load())

    def _load(self) -> list[dict[str, Any]]:
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def _save(self, rows: list[dict[str, Any]]) -> None:
        self.store_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _cosine_similarity(first: list[float], second: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(first, second))
        left = math.sqrt(sum(a * a for a in first))
        right = math.sqrt(sum(b * b for b in second))
        if left == 0 or right == 0:
            return 0.0
        return numerator / (left * right)


class MilvusVectorStore(VectorStore):
    backend_name = "milvus"

    def __init__(self, settings: Settings, dashscope_client: DashScopeClient) -> None:
        if connections is None or Collection is None or utility is None:
            raise RuntimeError("缺少 pymilvus 依赖")
        self.settings = settings
        self.dashscope_client = dashscope_client
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port,
            user=settings.milvus_username or None,
            password=settings.milvus_password or None,
        )
        self.collection = self._ensure_collection()

    def add_documents(self, documents: list[DocumentChunk]) -> None:
        embeddings = self.dashscope_client.embed([item.content for item in documents])
        rows = [
            [
                item.id,
                item.content,
                json.dumps(item.metadata, ensure_ascii=False),
                embedding,
            ]
            for item, embedding in zip(documents, embeddings)
        ]
        ids = [row[0] for row in rows]
        contents = [row[1] for row in rows]
        metadata = [row[2] for row in rows]
        vectors = [row[3] for row in rows]
        self.collection.insert([ids, contents, metadata, vectors])
        self.collection.flush()

    def similarity_search(self, query: str, top_k: int) -> list[DocumentChunk]:
        [query_embedding] = self.dashscope_client.embed([query])
        params = {"metric_type": self.settings.milvus_metric_type, "params": {"nprobe": 10}}
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=params,
            limit=top_k,
            output_fields=["content", "metadata"],
        )
        documents: list[DocumentChunk] = []
        for hit in results[0]:
            entity = hit.entity
            metadata = json.loads(entity.get("metadata") or "{}")
            documents.append(
                DocumentChunk(
                    id=str(hit.id),
                    content=entity.get("content"),
                    metadata=metadata,
                    score=float(hit.score),
                )
            )
        return documents

    def delete_documents(self, document_ids: list[str]) -> None:
        if document_ids:
            ids = ",".join(f'"{item}"' for item in document_ids)
            self.collection.delete(f'id in [{ids}]')

    def has_documents(self) -> bool:
        return self.collection.num_entities > 0

    def _ensure_collection(self) -> Collection:
        assert Collection is not None
        assert utility is not None
        if not utility.has_collection(self.settings.milvus_collection_name):
            schema = CollectionSchema(
                fields=[
                    FieldSchema(
                        name="id",
                        dtype=DataType.VARCHAR,
                        is_primary=True,
                        max_length=64,
                    ),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(
                        name="embedding",
                        dtype=DataType.FLOAT_VECTOR,
                        dim=self.settings.milvus_dimension,
                    ),
                ],
                description="RAG document chunks",
                enable_dynamic_field=False,
            )
            collection = Collection(name=self.settings.milvus_collection_name, schema=schema)
            index_params = {
                "index_type": self.settings.milvus_index_type,
                "metric_type": self.settings.milvus_metric_type,
                "params": {"nlist": 1024},
            }
            collection.create_index("embedding", index_params=index_params)
        else:
            collection = Collection(self.settings.milvus_collection_name)
        collection.load()
        return collection


def build_vector_store(settings: Settings, dashscope_client: DashScopeClient) -> VectorStore:
    backend = settings.vector_backend.lower()
    if backend == "local":
        return LocalVectorStore(settings, dashscope_client)
    if backend == "milvus":
        return MilvusVectorStore(settings, dashscope_client)
    try:
        return MilvusVectorStore(settings, dashscope_client)
    except Exception as exc:  # pragma: no cover
        logger.warning("Milvus unavailable, falling back to local store: %s", exc)
        return LocalVectorStore(settings, dashscope_client)
