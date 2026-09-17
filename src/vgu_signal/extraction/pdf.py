from __future__ import annotations

import io
import subprocess
from hashlib import sha256
from typing import cast
from urllib.parse import urljoin

import fitz
import pdfplumber
from pydantic import HttpUrl

from vgu_signal.domain import Document
from vgu_signal.extraction.common import (
    PARSER_VERSION,
    classify_notice,
    extract_dates,
    extract_deadlines,
    extract_events,
    normalize_text,
    source_relative_id,
)
from vgu_signal.extraction.models import (
    ExtractionKind,
    ExtractionQuality,
    ExtractedDocument,
    QualityLevel,
)

PDF_PARSER_VERSION = "pdf-pymupdf-v1+pdfplumber-crosscheck-v1"
OCR_PARSER_VERSION = "pdf-ocr-tesseract-v1"


def _metadata_tuple(metadata: dict[str, object]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(k), str(v)) for k, v in metadata.items() if v not in (None, "")))


def _quality(text: str, page_count: int, kind: ExtractionKind, warnings: tuple[str, ...] = ()) -> ExtractionQuality:
    length = len(text.strip())
    if length >= 400:
        score, level = 0.98, QualityLevel.HIGH
    elif length >= 100:
        score, level = 0.78, QualityLevel.MEDIUM
    elif length > 0:
        score, level = 0.45, QualityLevel.LOW
    else:
        score, level = 0.0, QualityLevel.FAILED
    return ExtractionQuality(level=level, score=score, text_length=length, page_count=page_count, extraction_kind=kind, warnings=warnings)


def _extract_pymupdf(body: bytes) -> tuple[str, dict[str, object], int]:
    with fitz.open(stream=body, filetype="pdf") as pdf:
        pages = [page.get_text("text") for page in pdf]
        metadata = dict(pdf.metadata)
        return normalize_text("\n".join(pages)), metadata, len(pdf)


def _extract_pdfplumber(body: bytes) -> str:
    with pdfplumber.open(io.BytesIO(body)) as pdf:
        return normalize_text("\n".join(page.extract_text() or "" for page in pdf.pages))


def _ocr(body: bytes) -> str:
    """Use the locally installed tesseract CLI only for genuinely text-poor PDFs."""
    try:
        process = subprocess.run(
            ["tesseract", "stdin", "stdout", "--dpi", "200"],
            input=body,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return normalize_text(process.stdout.decode("utf-8", errors="replace")) if process.returncode == 0 else ""


def extract_pdf(*, evidence_id: str, source_id: str, url: str, body: bytes) -> ExtractedDocument:
    warnings: list[str] = []
    try:
        text, metadata, page_count = _extract_pymupdf(body)
    except Exception as exc:
        text, metadata, page_count = "", {}, 1
        warnings.append(f"PyMuPDF extraction failed: {type(exc).__name__}")

    plumber_text = ""
    if text and len(text) < 100:
        try:
            plumber_text = _extract_pdfplumber(body)
            if len(plumber_text) > len(text):
                text = plumber_text
            elif plumber_text and plumber_text != text:
                warnings.append("pdfplumber cross-check differs from PyMuPDF")
        except Exception as exc:
            warnings.append(f"pdfplumber fallback failed: {type(exc).__name__}")
    elif text:
        try:
            plumber_text = _extract_pdfplumber(body)
            if plumber_text and plumber_text != text:
                warnings.append("pdfplumber cross-check differs from PyMuPDF")
        except Exception as exc:
            warnings.append(f"pdfplumber cross-check unavailable: {type(exc).__name__}")

    kind = ExtractionKind.PDF
    parser_version = PDF_PARSER_VERSION
    if len(text.strip()) < 100:
        ocr_text = _ocr(body)
        if ocr_text:
            text = ocr_text
            kind = ExtractionKind.OCR
            parser_version = OCR_PARSER_VERSION
        else:
            warnings.append("PDF contains too little extractable text and OCR was unavailable or unsuccessful")

    title = str(metadata.get("title") or "").strip() or f"VGU PDF document ({page_count} pages)"
    raw_hash = sha256(body).hexdigest()
    document_id = sha256(f"{source_id}:{url}:{raw_hash}:{parser_version}".encode()).hexdigest()
    relative_id = source_relative_id(source_id, url, raw_hash)
    dates = extract_dates(text)
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
        dates=dates,
        deadlines=extract_deadlines(text),
        events=extract_events(text),
        notice_category=classify_notice(text, title),
        source_relative_id=relative_id,
        quality=_quality(text, page_count, kind, tuple(warnings)),
    )


def to_document(extracted: ExtractedDocument) -> Document:
    return Document(
        id=extracted.id,
        evidence_id=extracted.evidence_id,
        source_id=extracted.source_id,
        canonical_url=extracted.canonical_url,
        title=extracted.title,
        published_at=None,
        body_text=extracted.body_text,
        links=extracted.links,
        parser_version=extracted.parser_version,
    )
