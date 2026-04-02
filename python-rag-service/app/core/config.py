# 导入未来版本注解
from __future__ import annotations

# 导入操作系统相关模块，用于读取环境变量（类似 Spring 的 Environment）
import os
# 导入 dataclass 装饰器，用于定义数据类（类似 Lombok 的 @Data + @ConfigurationProperties）
from dataclasses import dataclass
# 导入 LRU 缓存实现单例模式
from functools import lru_cache
# 导入路径处理模块
from pathlib import Path


# 辅助函数：从环境变量读取整数配置值
# 类似 Spring 的 environment.getProperty(name, Integer.class, defaultValue)
def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    # 如果环境变量存在且非空则转换为整数，否则返回默认值
    return int(value) if value not in (None, "") else default


# 辅助函数：从环境变量读取浮点数配置值
def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


# 使用 dataclass 定义配置类（类似 Spring 的 @ConfigurationProperties(prefix="...")）
# frozen=True 表示不可变对象（类似 Lombok 的 @Immutable）
@dataclass(frozen=True)
class Settings:
    # ==================== 应用基础配置 ====================
    # 应用名称，可通过 APP_NAME 环境变量覆盖
    app_name: str = os.getenv("APP_NAME", "rag-python-service")
    # 应用监听地址，0.0.0.0 表示监听所有网卡
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    # 应用端口号，默认 8080（类似 server.port）
    app_port: int = _env_int("SERVER_PORT", 8080)
    # CORS 允许的源域名列表
    cors_origins: list[str] = None  # type: ignore[assignment]

    # ==================== DashScope（阿里云通义千问）配置 ====================
    # API 密钥，用于调用阿里云百炼平台的大模型服务
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    # 聊天模型名称，默认 qwen-max（通义千问最大版本）
    dashscope_chat_model: str = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-max")
    # 嵌入模型名称，用于将文本转换为向量
    dashscope_embedding_model: str = os.getenv(
        "DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3"
    )
    # 模型温度参数，控制生成文本的随机性（0.7 为默认值）
    dashscope_temperature: float = _env_float("DASHSCOPE_TEMPERATURE", 0.7)

    # ==================== Milvus 向量数据库配置 ====================
    # Milvus 服务器地址
    milvus_host: str = os.getenv("MILVUS_HOST", "localhost")
    # Milvus 端口号
    milvus_port: int = _env_int("MILVUS_PORT", 19530)
    # Milvus 用户名（可选）
    milvus_username: str = os.getenv("MILVUS_USERNAME", "")
    # Milvus 密码（可选）
    milvus_password: str = os.getenv("MILVUS_PASSWORD", "")
    # Milvus 集合名称（类似数据库表名）
    milvus_collection_name: str = os.getenv("MILVUS_COLLECTION_NAME", "rag_documents")
    # 向量维度，必须与嵌入模型的输出维度一致
    milvus_dimension: int = _env_int("MILVUS_DIMENSION", 1536)
    # Milvus 索引类型（IVF_FLAT 为倒排平坦索引）
    milvus_index_type: str = os.getenv("MILVUS_INDEX_TYPE", "IVF_FLAT")
    # Milvus 度量类型（COSINE 表示余弦相似度）
    milvus_metric_type: str = os.getenv("MILVUS_METRIC_TYPE", "COSINE")

    # ==================== 向量存储后端配置 ====================
    # 向量存储后端类型：local（本地 JSON）或 milvus（Milvus 数据库）
    vector_backend: str = os.getenv("VECTOR_BACKEND", "auto")
    # 本地存储的文件路径（当使用 local 后端时）
    local_store_path: str = os.getenv(
        "LOCAL_VECTOR_STORE_PATH", "data/local_vector_store.json"
    )

    # ==================== 文档分块配置 ====================
    # 文档切片的最大字符数
    chunk_size: int = _env_int("CHUNK_SIZE", 1000)
    # 切片之间的重叠字符数（用于保持上下文连贯性）
    chunk_overlap: int = _env_int("CHUNK_OVERLAP", 120)

    # 后初始化方法：在 dataclass 的 __init__ 执行后自动调用
    # 类似 Spring 的 @PostConstruct，用于处理特殊配置逻辑
    def __post_init__(self) -> None:
        # 处理 CORS 源域名配置
        origins = os.getenv("CORS_ORIGINS", "*")
        # 由于 frozen=True，需要使用 object.__setattr__ 来修改字段
        object.__setattr__(
            self,
            "cors_origins",
            # 如果是 "*" 则允许所有来源，否则解析逗号分隔的域名列表
            ["*"] if origins == "*" else [item.strip() for item in origins.split(",") if item.strip()],
        )
        
        # 处理本地存储路径：相对路径转换为绝对路径
        store_path = Path(self.local_store_path)
        if not store_path.is_absolute():
            # 获取项目根目录（当前文件的祖父目录）
            root = Path(__file__).resolve().parents[2]
            # 将相对路径拼接为绝对路径
            object.__setattr__(self, "local_store_path", str(root / store_path))


# 使用 LRU 缓存实现 Settings 单例（类似 Spring 的 @ConfigurationProperties 单例 Bean）
# maxsize=1 确保整个应用只创建一个 Settings 实例
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # 创建并返回配置实例（首次调用后会被缓存）
    return Settings()
