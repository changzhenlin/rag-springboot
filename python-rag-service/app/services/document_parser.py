from __future__ import annotations

import csv
import io
import json
import logging
import uuid
from pathlib import Path
from typing import Callable

from bs4 import BeautifulSoup

from app.core.config import Settings
from app.models.schemas import DocumentChunk

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:  # pragma: no cover
    DocxDocument = None

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover
    load_workbook = None

try:
    from pptx import Presentation
except ImportError:  # pragma: no cover
    Presentation = None


class DocumentParserError(Exception):
    pass


class DocumentParserService:
    SUPPORTED_TYPES = {
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
        "txt",
        "html",
        "xml",
        "md",
        "csv",
        "json",
    }

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @classmethod
    def is_supported(cls, filename: str | None) -> bool:
        if not filename or "." not in filename:
            return False
        return filename.rsplit(".", 1)[1].lower() in cls.SUPPORTED_TYPES

    def parse_upload(self, filename: str, content: bytes, content_type: str | None) -> list[DocumentChunk]:
        text = self._extract_text(filename, content)
        metadata = {
            "source": filename,
            "fileSize": len(content),
            "contentType": content_type or "application/octet-stream",
        }
        return self._split_text(text, metadata)

    def parse_path(self, path: str | Path) -> list[DocumentChunk]:
        file_path = Path(path)
        content = file_path.read_bytes()
        text = self._extract_text(file_path.name, content)
        metadata = {"source": file_path.name, "filePath": str(file_path)}
        return self._split_text(text, metadata)

    def _extract_text(self, filename: str, content: bytes) -> str:
        ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
        parsers: dict[str, Callable[[bytes], str]] = {
            "txt": self._parse_text,
            "md": self._parse_text,
            "json": self._parse_json,
            "csv": self._parse_csv,
            "html": self._parse_html,
            "xml": self._parse_html,
            "pdf": self._parse_pdf,
            "docx": self._parse_docx,
            "xlsx": self._parse_xlsx,
            "pptx": self._parse_pptx,
            "doc": self._parse_legacy_binary,
            "xls": self._parse_legacy_binary,
            "ppt": self._parse_legacy_binary,
        }
        parser = parsers.get(ext)
        if parser is None:
            raise DocumentParserError(f"不支持的文件类型: {ext}")
        text = parser(content).strip()
        if not text:
            raise DocumentParserError("文档解析后内容为空")
        return text

    def _parse_text(self, content: bytes) -> str:
        return content.decode("utf-8", errors="ignore")

    def _parse_json(self, content: bytes) -> str:
        payload = json.loads(content.decode("utf-8", errors="ignore"))
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _parse_csv(self, content: bytes) -> str:
        reader = csv.reader(io.StringIO(content.decode("utf-8", errors="ignore")))
        return "\n".join([", ".join(row) for row in reader])

    def _parse_html(self, content: bytes) -> str:
        soup = BeautifulSoup(content.decode("utf-8", errors="ignore"), "html.parser")
        return soup.get_text(separator="\n")

    def _parse_pdf(self, content: bytes) -> str:
        if PdfReader is None:
            raise DocumentParserError("缺少 pypdf 依赖，无法解析 PDF")
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _parse_docx(self, content: bytes) -> str:
        if DocxDocument is None:
            raise DocumentParserError("缺少 python-docx 依赖，无法解析 DOCX")
        document = DocxDocument(io.BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    def _parse_xlsx(self, content: bytes) -> str:
        if load_workbook is None:
            raise DocumentParserError("缺少 openpyxl 依赖，无法解析 XLSX")
        workbook = load_workbook(io.BytesIO(content), data_only=True)
        rows: list[str] = []
        for sheet in workbook.worksheets:
            rows.append(f"[Sheet] {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                cells = [str(cell) for cell in row if cell is not None]
                if cells:
                    rows.append(" | ".join(cells))
        return "\n".join(rows)

    def _parse_pptx(self, content: bytes) -> str:
        if Presentation is None:
            raise DocumentParserError("缺少 python-pptx 依赖，无法解析 PPTX")
        presentation = Presentation(io.BytesIO(content))
        lines: list[str] = []
        for index, slide in enumerate(presentation.slides, start=1):
            lines.append(f"[Slide {index}]")
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    lines.append(shape.text)
        return "\n".join(lines)

    def _parse_legacy_binary(self, _: bytes) -> str:
        raise DocumentParserError("旧版 Office 二进制格式暂不支持，请转换为 docx/xlsx/pptx 后上传")

    def _split_text(self, text: str, metadata: dict[str, object]) -> list[DocumentChunk]:
        normalized = " ".join(text.split())
        chunk_size = max(self.settings.chunk_size, 200)
        overlap = min(self.settings.chunk_overlap, chunk_size // 2)
        chunks: list[DocumentChunk] = []
        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + chunk_size)
            content = normalized[start:end].strip()
            if content:
                chunk_metadata = dict(metadata)
                chunk_metadata["chunkIndex"] = len(chunks)
                chunks.append(
                    DocumentChunk(
                        id=str(uuid.uuid4()),
                        content=content,
                        metadata=chunk_metadata,
                    )
                )
            if end >= len(normalized):
                break
            start = end - overlap
        logger.info("document split into %s chunks", len(chunks))
        return chunks
