from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from app.dependencies import get_document_parser_service, get_rag_service, get_vector_store
from app.models.schemas import ApiResponse, AskResult, DocumentChunk, HealthResult, QuestionRequest, UploadResult
from app.services.document_parser import DocumentParserError, DocumentParserService
from app.services.rag_service import RagService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/upload", response_model=ApiResponse[UploadResult])
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    parser_service: Annotated[DocumentParserService, Depends(get_document_parser_service)],
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
) -> ApiResponse[UploadResult]:
    if not parser_service.is_supported(file.filename):
        return JSONResponse(
            status_code=400,
            content=ApiResponse.error("不支持的文件类型", code=400).model_dump(),
        )
    try:
        content = await file.read()
        documents = parser_service.parse_upload(file.filename or "unknown", content, file.content_type)
        vector_store.add_documents(documents)
        return ApiResponse.success(
            UploadResult(
                fileName=file.filename or "unknown",
                chunksCount=len(documents),
                fileSize=len(content),
            ),
            message="文档上传成功",
        )
    except DocumentParserError as exc:
        logger.exception("document parse failed")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(f"文档解析失败: {exc}").model_dump(),
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("document upload failed")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(f"文档上传失败: {exc}").model_dump(),
        )


@router.post("/ask", response_model=ApiResponse[AskResult])
async def ask_question(
    request: QuestionRequest,
    rag_service: Annotated[RagService, Depends(get_rag_service)],
) -> ApiResponse[AskResult]:
    try:
        answer = rag_service.ask(request.question, request.topK)
        return ApiResponse.success(AskResult(question=request.question, answer=answer))
    except Exception as exc:  # pragma: no cover
        logger.exception("rag ask failed")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(f"问答处理失败: {exc}").model_dump(),
        )


@router.get("/search", response_model=ApiResponse[list[DocumentChunk]])
async def search_similar(
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
    query: str,
    topK: int = 4,
) -> ApiResponse[list[DocumentChunk]]:
    try:
        documents = vector_store.similarity_search(query, topK)
        return ApiResponse.success(documents)
    except Exception as exc:  # pragma: no cover
        logger.exception("search failed")
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(f"搜索失败: {exc}").model_dump(),
        )


@router.get("/health", response_model=ApiResponse[HealthResult])
async def health(
    vector_store: Annotated[VectorStore, Depends(get_vector_store)],
) -> ApiResponse[HealthResult]:
    return ApiResponse.success(
        HealthResult(
            status="UP",
            hasDocuments=vector_store.has_documents(),
            vectorBackend=vector_store.backend_name,
        )
    )
