from __future__ import annotations

from hashlib import sha256
from typing import cast

from pydantic import HttpUrl

from vgu_signal.extraction.common import (
    PARSER_VERSION,
    classify_notice,
    extract_dates,
    extract_deadlines,
    extract_events,
    normalize_text,
    source_relative_id,
)
from vgu_signal.extraction.html import extract_document as extract_html
from vgu_signal.extraction.models import ExtractionKind, ExtractionQuality, ExtractedDocument, QualityLevel
from vgu_signal.extraction.pdf import extract_pdf

_HTML_TYPES = {"text/html", "application/xhtml+xml"}
_PDF_TYPES = {"application/pdf"}
_TEXT_TYPES = {"text/plain", "application/xml", "text/xml"}


def normalize_content_type(content_type: str) -> str:
    return content_type.split(";", 1)[0].strip().lower()


def extract_evidence(*, evidence_id: str, source_id: str, url: str, content_type: str, body: bytes) -> ExtractedDocument:
    media_type = normalize_content_type(content_type)
    if media_type in _HTML_TYPES:
        return extract_html(evidence_id=evidence_id, source_id=source_id, url=url, body=body)
    if media_type in _PDF_TYPES:
        return extract_pdf(evidence_id=evidence_id, source_id=source_id, url=url, body=body)
    if media_type in _TEXT_TYPES:
        text = normalize_text(body.decode("utf-8", errors="replace"))
        raw_hash = sha256(body).hexdigest()
        score = 0.8 if text else 0.0
        quality = ExtractionQuality(
            level=QualityLevel.MEDIUM if text else QualityLevel.FAILED,
            score=score,
            text_length=len(text),
            page_count=None,
            extraction_kind=ExtractionKind.TEXT,
        )
        return ExtractedDocument(
            id=sha256(f"{source_id}:{url}:{raw_hash}:{PARSER_VERSION}".encode()).hexdigest(),
            evidence_id=evidence_id,
            source_id=source_id,
            canonical_url=cast(HttpUrl, url),
            title="VGU text document",
            body_text=text,
            parser_version=PARSER_VERSION,
            extraction_kind=ExtractionKind.TEXT,
            dates=extract_dates(text),
            deadlines=extract_deadlines(text),
            events=extract_events(text),
            notice_category=classify_notice(text),
            source_relative_id=source_relative_id(source_id, url, raw_hash),
            quality=quality,
        )
    raise ValueError(f"unsupported extraction content type: {content_type!r}")
