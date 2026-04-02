# 导入未来版本注解
from __future__ import annotations

# 导入必要的库
import json
import logging
import math
# 导入 ABC 抽象基类（类似 Java 的 abstract class）
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# 导入配置类
from app.core.config import Settings
# 导入文档切片模型
from app.models.schemas import DocumentChunk
# 导入 DashScope 客户端
from app.services.dashscope_client import DashScopeClient

# 创建日志记录器
logger = logging.getLogger(__name__)

# 尝试导入 Milvus 向量数据库 SDK
try:
    from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility
except ImportError:  # pragma: no cover
    # 如果未安装则设为 None
    Collection = None
    CollectionSchema = None
    DataType = None
    FieldSchema = None
    connections = None
    utility = None


# 向量存储抽象基类：定义向量存储的通用接口（类似 Java 的 interface）
class VectorStore(ABC):
    # 后端名称标识
    backend_name: str = "unknown"

    # 抽象方法：添加文档到向量库
    @abstractmethod
    def add_documents(self, documents: list[DocumentChunk]) -> None:
        raise NotImplementedError

    # 抽象方法：相似度搜索
    @abstractmethod
    def similarity_search(self, query: str, top_k: int) -> list[DocumentChunk]:
        raise NotImplementedError

    # 抽象方法：删除文档
    @abstractmethod
    def delete_documents(self, document_ids: list[str]) -> None:
        raise NotImplementedError

    # 抽象方法：检查是否有文档
    @abstractmethod
    def has_documents(self) -> bool:
        raise NotImplementedError


# 本地向量存储实现：使用 JSON 文件存储向量数据（适合开发和测试）
class LocalVectorStore(VectorStore):
    # 后端名称：local
    backend_name = "local"

    def __init__(self, settings: Settings, dashscope_client: DashScopeClient) -> None:
        # 保存配置和客户端引用
        self.settings = settings
        self.dashscope_client = dashscope_client
        # 获取本地存储文件路径
        self.store_path = Path(settings.local_store_path)
        # 确保父目录存在
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        # 如果文件不存在则创建空文件
        if not self.store_path.exists():
            self.store_path.write_text("[]", encoding="utf-8")

    # 添加文档：将文档切片向量化并保存到 JSON 文件
    def add_documents(self, documents: list[DocumentChunk]) -> None:
        # 加载现有数据
        rows = self._load()
        # 使用 DashScope 生成所有文档的向量嵌入
        embeddings = self.dashscope_client.embed([item.content for item in documents])
        # 将每个文档与其向量配对并添加到列表
        for item, embedding in zip(documents, embeddings):
            rows.append(
                {
                    "id": item.id,
                    "content": item.content,
                    "metadata": item.metadata,
                    "embedding": embedding,  # 向量数据
                }
            )
        # 保存到 JSON 文件
        self._save(rows)

    # 相似度搜索：在本地 JSON 数据中查找最相似的文档
    def similarity_search(self, query: str, top_k: int) -> list[DocumentChunk]:
        # 加载所有数据
        rows = self._load()
        if not rows:
            return []
        # 将查询文本转换为向量
        [query_embedding] = self.dashscope_client.embed([query])
        # 按余弦相似度排序，取前 top_k 个
        ranked = sorted(
            rows,
            key=lambda row: self._cosine_similarity(query_embedding, row["embedding"]),
            reverse=True,
        )[:top_k]
        # 构建返回结果（包含相似度分数）
        return [
            DocumentChunk(
                id=row["id"],
                content=row["content"],
                metadata=row.get("metadata", {}),
                score=self._cosine_similarity(query_embedding, row["embedding"]),
            )
            for row in ranked
        ]

    # 删除文档：从 JSON 文件中移除指定 ID 的文档
    def delete_documents(self, document_ids: list[str]) -> None:
        # 过滤掉要删除的 ID
        rows = [row for row in self._load() if row["id"] not in set(document_ids)]
        self._save(rows)

    # 检查是否有文档
    def has_documents(self) -> bool:
        return bool(self._load())

    # 私有方法：从 JSON 文件加载数据
    def _load(self) -> list[dict[str, Any]]:
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    # 私有方法：保存数据到 JSON 文件
    def _save(self, rows: list[dict[str, Any]]) -> None:
        self.store_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # 静态方法：计算两个向量的余弦相似度
    # 值域 [-1, 1]，越接近 1 表示越相似
    @staticmethod
    def _cosine_similarity(first: list[float], second: list[float]) -> float:
        # 计算点积
        numerator = sum(a * b for a, b in zip(first, second))
        # 计算两个向量的模
        left = math.sqrt(sum(a * a for a in first))
        right = math.sqrt(sum(b * b for b in second))
        if left == 0 or right == 0:
            return 0.0
        # 返回余弦相似度
        return numerator / (left * right)


# Milvus 向量数据库实现：使用专业的向量数据库（适合生产环境）
class MilvusVectorStore(VectorStore):
    # 后端名称：milvus
    backend_name = "milvus"

    def __init__(self, settings: Settings, dashscope_client: DashScopeClient) -> None:
        # 检查依赖是否已安装
        if connections is None or Collection is None or utility is None:
            raise RuntimeError("缺少 pymilvus 依赖")
        # 保存配置和客户端引用
        self.settings = settings
        self.dashscope_client = dashscope_client
        
        # 连接到 Milvus 服务器
        connections.connect(
            alias="default",  # 连接别名
            host=settings.milvus_host,  # Milvus 主机地址
            port=settings.milvus_port,  # Milvus 端口
            user=settings.milvus_username or None,  # 用户名（可选）
            password=settings.milvus_password or None,  # 密码（可选）
        )
        # 确保集合（表）存在
        self.collection = self._ensure_collection()

    # 添加文档：向量化并插入 Milvus 集合
    def add_documents(self, documents: list[DocumentChunk]) -> None:
        # 生成所有文档的向量嵌入
        embeddings = self.dashscope_client.embed([item.content for item in documents])
        # 构建批量插入的数据行
        rows = [
            [
                item.id,  # ID 列
                item.content,  # 内容列
                json.dumps(item.metadata, ensure_ascii=False),  # 元数据列（JSON 字符串）
                embedding,  # 向量列
            ]
            for item, embedding in zip(documents, embeddings)
        ]
        # 分离各列数据
        ids = [row[0] for row in rows]
        contents = [row[1] for row in rows]
        metadata = [row[2] for row in rows]
        vectors = [row[3] for row in rows]
        # 批量插入数据
        self.collection.insert([ids, contents, metadata, vectors])
        # 刷新到磁盘
        self.collection.flush()

    # 相似度搜索：使用 Milvus 的 ANN（近似最近邻）搜索
    def similarity_search(self, query: str, top_k: int) -> list[DocumentChunk]:
        # 将查询转换为向量
        [query_embedding] = self.dashscope_client.embed([query])
        # 配置搜索参数
        params = {"metric_type": self.settings.milvus_metric_type, "params": {"nprobe": 10}}
        # 执行搜索
        results = self.collection.search(
            data=[query_embedding],  # 查询向量
            anns_field="embedding",  # 搜索的向量字段
            param=params,  # 搜索参数
            limit=top_k,  # 返回数量限制
            output_fields=["content", "metadata"],  # 需要返回的字段
        )
        # 构建结果列表
        documents: list[DocumentChunk] = []
        for hit in results[0]:
            entity = hit.entity  # 获取实体数据
            metadata = json.loads(entity.get("metadata") or "{}")
            documents.append(
                DocumentChunk(
                    id=str(hit.id),
                    content=entity.get("content"),
                    metadata=metadata,
                    score=float(hit.score),  # 相似度分数
                )
            )
        return documents

    # 删除文档：从 Milvus 中删除指定 ID 的文档
    def delete_documents(self, document_ids: list[str]) -> None:
        if document_ids:
            # 构建删除表达式：id in ["id1", "id2", ...]
            ids = ",".join(f'"{item}"' for item in document_ids)
            self.collection.delete(f'id in [{ids}]')

    # 检查是否有文档：通过实体数量判断
    def has_documents(self) -> bool:
        return self.collection.num_entities > 0

    # 私有方法：确保集合（表）存在，不存在则创建
    def _ensure_collection(self) -> Collection:
        assert Collection is not None
        assert utility is not None
        
        # 检查集合是否存在
        if not utility.has_collection(self.settings.milvus_collection_name):
            # 定义集合 Schema（类似数据库表结构）
            schema = CollectionSchema(
                fields=[
                    FieldSchema(
                        name="id",
                        dtype=DataType.VARCHAR,  # 字符串类型
                        is_primary=True,  # 主键
                        max_length=64,  # 最大长度
                    ),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),  # 内容字段
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),  # 元数据字段
                    FieldSchema(
                        name="embedding",  # 向量字段
                        dtype=DataType.FLOAT_VECTOR,  # 浮点向量类型
                        dim=self.settings.milvus_dimension,  # 向量维度
                    ),
                ],
                description="RAG document chunks",  # 集合描述
                enable_dynamic_field=False,  # 禁用动态字段
            )
            # 创建集合
            collection = Collection(name=self.settings.milvus_collection_name, schema=schema)
            
            # 创建索引以加速搜索
            index_params = {
                "index_type": self.settings.milvus_index_type,  # 索引类型
                "metric_type": self.settings.milvus_metric_type,  # 度量类型
                "params": {"nlist": 1024},  # 索引参数
            }
            collection.create_index("embedding", index_params=index_params)
        else:
            # 如果集合已存在，直接获取
            collection = Collection(self.settings.milvus_collection_name)
        
        # 加载集合到内存
        collection.load()
        return collection


# 工厂函数：根据配置构建合适的向量存储实例
# 类似 Spring 的工厂 Bean 模式
def build_vector_store(settings: Settings, dashscope_client: DashScopeClient) -> VectorStore:
    # 获取配置的后端类型并转为小写
    backend = settings.vector_backend.lower()
    # 如果配置为 local，使用本地 JSON 存储
    if backend == "local":
        return LocalVectorStore(settings, dashscope_client)
    # 如果配置为 milvus，使用 Milvus 数据库
    if backend == "milvus":
        return MilvusVectorStore(settings, dashscope_client)
    
    # 如果是 auto 或其他值，尝试使用 Milvus，失败则降级到本地存储
    try:
        return MilvusVectorStore(settings, dashscope_client)
    except Exception as exc:  # pragma: no cover
        logger.warning("Milvus unavailable, falling back to local store: %s", exc)
        return LocalVectorStore(settings, dashscope_client)
