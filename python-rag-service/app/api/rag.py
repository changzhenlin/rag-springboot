# 导入未来版本注解
from __future__ import annotations

# 导入日志模块
import logging
# 导入类型注解
from typing import Annotated

# 从 fastapi 导入路由相关类
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

# 导入依赖注入函数（类似 Spring 的 @Autowired）
from app.dependencies import get_document_parser_service, get_rag_service, get_vector_store
# 导入数据模型
from app.models.schemas import ApiResponse, AskResult, DocumentChunk, HealthResult, QuestionRequest, UploadResult
# 导入文档解析服务和错误类
from app.services.document_parser import DocumentParserError, DocumentParserService
# 导入 RAG 服务
from app.services.rag_service import RagService
from app.services.vector_store import VectorStore

# 创建日志记录器（类似 SLF4J 的 Logger）
logger = logging.getLogger(__name__)

# 创建 APIRouter 实例（类似 Spring 的 @RestController）
# prefix="/api/rag" 表示所有路由的前缀
# tags=["rag"] 用于 OpenAPI/Swagger 文档分组
router = APIRouter(prefix="/api/rag", tags=["rag"])


# 上传文档接口：POST /api/rag/upload
# async 关键字表示这是一个异步方法（类似 Spring WebFlux 的响应式编程）
@router.post("/upload", response_model=ApiResponse[UploadResult])
async def upload_document(
    # Annotated 是 Python 3.9+ 的类型注解语法，用于依赖注入
    # file: UploadFile 表示上传的文件（类似 MultipartFile）
    # File(...) 表示这是表单文件字段
    file: Annotated[UploadFile, File(...)],
    # parser_service: 通过 Depends 注入文档解析服务（类似 @Autowired）
    parser_service: Annotated[DocumentParserService, Depends(get_document_parser_service)],
    # vector_store: 注入向量存储服务
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
) -> ApiResponse[UploadResult]:
    # 检查文件类型是否支持
    if not parser_service.is_supported(file.filename):
        # 返回 400 错误响应
        return JSONResponse(
            status_code=400,
            content=ApiResponse.error("不支持的文件类型", code=400).model_dump(),
        )
    try:
        # 异步读取文件内容
        content = await file.read()
        # 解析上传的文件，提取文本并分块
        documents = parser_service.parse_upload(file.filename or "unknown", content, file.content_type)
        # 将文档切片添加到向量存储中
        vector_store.add_documents(documents)
        # 返回成功响应
        return ApiResponse.success(
            UploadResult(
                fileName=file.filename or "unknown",
                chunksCount=len(documents),  # 返回切片数量
                fileSize=len(content),  # 返回文件大小
            ),
            message="文档上传成功",
        )
    except DocumentParserError as exc:
        # 记录解析失败的异常日志
        logger.exception("document parse failed")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(f"文档解析失败：{exc}").model_dump(),
        )
    except Exception as exc:  # pragma: no cover
        # 捕获其他未预期的异常
        logger.exception("document upload failed")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(f"文档上传失败：{exc}").model_dump(),
        )


# 问答接口：POST /api/rag/ask
@router.post("/ask", response_model=ApiResponse[AskResult])
async def ask_question(
    # request: 接收 JSON 请求体（类似 @RequestBody）
    request: QuestionRequest,
    # rag_service: 注入 RAG 服务
    rag_service: Annotated[RagService, Depends(get_rag_service)],
) -> ApiResponse[AskResult]:
    try:
        # 调用 RAG 服务进行问答：先检索相关文档，再让 AI 生成答案
        answer = rag_service.ask(request.question, request.topK)
        # 返回包含问题和答案的响应
        return ApiResponse.success(AskResult(question=request.question, answer=answer))
    except Exception as exc:  # pragma: no cover
        # 记录异常日志
        logger.exception("rag ask failed")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(f"问答处理失败：{exc}").model_dump(),
        )


# 相似度搜索接口：GET /api/rag/search?query=xxx&topK=4
@router.get("/search", response_model=ApiResponse[list[DocumentChunk]])
async def search_similar(
    # vector_store: 注入向量存储服务
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
    # query: 查询参数（URL 中的 ?query=xxx）
    query: str,
    # topK: 返回结果数量，默认 4 个
    topK: int = 4,
) -> ApiResponse[list[DocumentChunk]]:
    try:
        # 在向量数据库中搜索与查询最相似的文档切片
        documents = vector_store.similarity_search(query, topK)
        # 返回搜索结果（包含相似度分数）
        return ApiResponse.success(documents)
    except Exception as exc:  # pragma: no cover
        logger.exception("search failed")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(f"搜索失败：{exc}").model_dump(),
        )


# 健康检查接口：GET /api/rag/health（类似 Spring Boot Actuator）
@router.get("/health", response_model=ApiResponse[HealthResult])
async def health(
    # vector_store: 注入向量存储服务
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
) -> ApiResponse[HealthResult]:
    # 返回服务状态、是否有文档、使用的向量存储后端
    return ApiResponse.success(
        HealthResult(
            status="UP",  # 服务状态正常
            hasDocuments=vector_store.has_documents(),  # 检查是否有文档数据
            vectorBackend=vector_store.backend_name,  # local 或 milvus
        )
    )
