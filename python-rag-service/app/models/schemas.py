from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Any, message: str = "操作成功") -> "ApiResponse[Any]":
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: int = 500) -> "ApiResponse[Any]":
        return cls(code=code, message=message, data=None)


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)
    topK: int = Field(default=4, ge=1, le=20)


class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None


class UploadResult(BaseModel):
    fileName: str
    chunksCount: int
    fileSize: int


class AskResult(BaseModel):
    question: str
    answer: str


class HealthResult(BaseModel):
    status: str
    hasDocuments: bool
    vectorBackend: str


class TestResult(BaseModel):
    success: bool
    method: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    error: Optional[str] = None
    message: str
    modelStatus: Optional[str] = None
