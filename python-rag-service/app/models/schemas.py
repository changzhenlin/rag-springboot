# 导入未来版本注解
from __future__ import annotations

# 导入类型提示工具
from typing import Any, Generic, Optional, TypeVar

# 从 pydantic 导入 BaseModel 和 Field，用于定义数据模型（类似 Lombok 的 @Data + Spring 的 DTO）
from pydantic import BaseModel, Field

# 定义泛型类型变量 T（类似 Java 的 <T>）
T = TypeVar("T")


# 通用 API 响应封装类（类似 Spring Boot 的 ApiResponse<T>）
# 使用泛型支持不同的数据类型
class ApiResponse(BaseModel, Generic[T]):
    # HTTP 状态码（200 成功，500 错误等）
    code: int
    # 响应消息
    message: str
    # 响应数据，可选字段
    data: Optional[T] = None

    # 类方法：构造成功响应（类似静态工厂方法）
    @classmethod
    def success(cls, data: Any, message: str = "操作成功") -> "ApiResponse[Any]":
        return cls(code=200, message=message, data=data)

    # 类方法：构造错误响应
    @classmethod
    def error(cls, message: str, code: int = 500) -> "ApiResponse[Any]":
        return cls(code=code, message=message, data=None)


# 问答请求 DTO（类似 Spring 的 @RequestBody 接收的对象）
class QuestionRequest(BaseModel):
    # 用户问题，必填字段，最小长度 1
    question: str = Field(..., min_length=1)
    # 返回结果数量，默认 4 个，范围 1-20
    topK: int = Field(default=4, ge=1, le=20)


# 文档切片 DTO：表示从文档中截取的一段内容
class DocumentChunk(BaseModel):
    # 唯一标识符（UUID）
    id: str
    # 文本内容
    content: str
    # 元数据信息（来源文件、页码等），默认为空字典
    metadata: dict[str, Any] = Field(default_factory=dict)
    # 相似度分数（仅在搜索时返回）
    score: Optional[float] = None


# 文件上传结果 DTO
class UploadResult(BaseModel):
    # 文件名
    fileName: str
    # 切片数量
    chunksCount: int
    # 文件大小（字节）
    fileSize: int


# 问答结果 DTO
class AskResult(BaseModel):
    # 用户问题
    question: str
    # AI 生成的答案
    answer: str


# 健康检查结果 DTO（类似 Spring Boot Actuator 的 /health 端点）
class HealthResult(BaseModel):
    # 服务状态（UP/DOWN）
    status: str
    # 是否有文档数据
    hasDocuments: bool
    # 向量存储后端类型（local/milvus）
    vectorBackend: str


# 测试功能结果 DTO
class TestResult(BaseModel):
    # 测试是否成功
    success: bool
    # 测试方法名称
    method: Optional[str] = None
    # 测试问题
    question: Optional[str] = None
    # AI 回答
    answer: Optional[str] = None
    # 错误信息（失败时）
    error: Optional[str] = None
    # 响应消息
    message: str
    # 模型状态
    modelStatus: Optional[str] = None
