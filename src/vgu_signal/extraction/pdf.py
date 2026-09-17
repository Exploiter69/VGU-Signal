from __future__ import annotations

import io
import subprocess
from hashlib import sha256
from typing import cast

import fitz  # type: ignore[import-untyped]
import pdfplumber
from pydantic import HttpUrl

from vgu_signal.domain import Document
from vgu_signal.extraction.common import (
    classify_notice,
    extract_dates,
    extract_deadlines,
    extract_events,
    normalize_text,
    source_relative_id,
)
from vgu_signal.extraction.models import (
    ExtractedDocument,
    ExtractionKind,
    ExtractionQuality,
    QualityLevel,
)

PDF_PARSER_VERSION = "pdf-pymupdf-v1+pdfplumber-crosscheck-v1"
OCR_PARSER_VERSION = "pdf-ocr-tesseract-v1"


def _metadata_tuple(metadata: dict[str, object]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(k), str(v)) for k, v in metadata.items() if v not in (None, "")))


def _quality(
    text: str, page_count: int, kind: ExtractionKind, warnings: tuple[str, ...] = ()
) -> ExtractionQuality:
    length = len(text.strip())
    if length >= 400:
        score, level = 0.98, QualityLevel.HIGH
    elif length >= 100:
        score, level = 0.78, QualityLevel.MEDIUM
    elif length > 0:
        score, level = 0.45, QualityLevel.LOW
    else:
        score, level = 0.0, QualityLevel.FAILED
    return ExtractionQuality(
        level=level,
        score=score,
        text_length=length,
        page_count=page_count,
        extraction_kind=kind,
        warnings=warnings,
    )


def _extract_pymupdf(body: bytes) -> tuple[str, dict[str, object], int]:
    with fitz.open(stream=body, filetype="pdf") as pdf:
        pages = [page.get_text("text") for page in pdf]
        return normalize_text("\n".join(pages)), dict(pdf.metadata), len(pdf)


def _extract_pdfplumber(body: bytes) -> str:
    with pdfplumber.open(io.BytesIO(body)) as pdf:
        return normalize_text("\n".join(page.extract_text() or "" for page in pdf.pages))


def _ocr(body: bytes) -> str:
    """Render scanned pages locally and invoke the optional tesseract CLI."""
    try:
        with fitz.open(stream=body, filetype="pdf") as pdf:
            chunks: list[str] = []
            for page in pdf:
                pixmap = page.get_pixmap(dpi=150, alpha=False)
                try:
                    process = subprocess.run(
                        ["tesseract", "stdin", "stdout", "--dpi", "150"],
                        input=pixmap.tobytes("png"),
                        capture_output=True,
                        check=False,
                        timeout=30,
                    )
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    return ""
                if process.returncode == 0:
                    chunks.append(process.stdout.decode("utf-8", errors="replace"))
            return normalize_text("\n".join(chunks))
    except Exception:
        return ""


def extract_pdf(*, evidence_id: str, source_id: str, url: str, body: bytes) -> ExtractedDocument:
    warnings: list[str] = []
    try:
        text, metadata, page_count = _extract_pymupdf(body)
    except Exception as exc:
        text, metadata, page_count = "", {}, 1
        warnings.append(f"PyMuPDF extraction failed: {type(exc).__name__}")

    if text:
        try:
            plumber_text = _extract_pdfplumber(body)
            if len(plumber_text) > len(text):
                text = plumber_text
                warnings.append("pdfplumber supplied more text than PyMuPDF")
            elif plumber_text and plumber_text != text:
                warnings.append("pdfplumber cross-check differs from PyMuPDF")
        except Exception as exc:
            warnings.append(f"pdfplumber cross-check unavailable: {type(exc).__name__}")
    else:
        try:
            text = _extract_pdfplumber(body)
        except Exception as exc:
            warnings.append(f"pdfplumber fallback failed: {type(exc).__name__}")

    kind = ExtractionKind.PDF
    parser_version = PDF_PARSER_VERSION
    if len(text.strip()) < 100:
        ocr_text = _ocr(body)
        if ocr_text:
            text = ocr_text
            kind = ExtractionKind.OCR
            parser_version = OCR_PARSER_VERSION
        else:
            warnings.append("PDF text is too sparse and OCR was unavailable or unsuccessful")

    title = str(metadata.get("title") or "").strip() or f"VGU PDF document ({page_count} pages)"
    raw_hash = sha256(body).hexdigest()
    document_id = sha256(f"{source_id}:{url}:{raw_hash}:{parser_version}".encode()).hexdigest()
    return ExtractedDocument(
        id=document_id,
        evidence_id=evidence_id,
        source_id=source_id,
        canonical_url=cast(HttpUrl, url),
        title=title,
        body_text=text,
        links=(),
        parser_version=parser_version,
        extraction_kind=kind,
        metadata=_metadata_tuple(metadata),
        dates=extract_dates(text),
        deadlines=extract_deadlines(text),
        events=extract_events(text),
        notice_category=classify_notice(text, title),
        source_relative_id=source_relative_id(source_id, url, raw_hash),
        quality=_quality(text, page_count, kind, tuple(warnings)),
    )


def to_document(extracted: ExtractedDocument) -> Document:
    return Document(
        id=extracted.id,
        evidence_id=extracted.evidence_id,
        source_id=extracted.source_id,
        canonical_url=extracted.canonical_url,
        title=extracted.title,
        published_at=extracted.published_at,
        body_text=extracted.body_text,
        links=extracted.links,
        parser_version=extracted.parser_version,
    )
