from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ExtractionKind(StrEnum):
    HTML = "HTML"
    PDF = "PDF"
    OCR = "OCR"
    TEXT = "TEXT"


class QualityLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    FAILED = "FAILED"


class NoticeCategory(StrEnum):
    ACADEMIC = "ACADEMIC"
    EXAMINATION = "EXAMINATION"
    FEES = "FEES"
    REGISTRATION = "REGISTRATION"
    EVENT = "EVENT"
    HOLIDAY = "HOLIDAY"
    GENERAL = "GENERAL"
    UNKNOWN = "UNKNOWN"


class ExtractedDate(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: datetime
    label: str = Field(min_length=1)
    source_text: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class ExtractedDeadline(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str = Field(min_length=1)
    due_at: datetime
    source_text: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class ExtractedEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime | None = None
    source_text: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class ExtractionQuality(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: QualityLevel
    score: float = Field(ge=0, le=1)
    text_length: int = Field(ge=0)
    page_count: int | None = Field(default=None, ge=1)
    extraction_kind: ExtractionKind
    warnings: tuple[str, ...] = ()


class ExtractedDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    canonical_url: HttpUrl
    title: str = Field(min_length=1)
    published_at: datetime | None = None
    body_text: str = ""
    links: tuple[HttpUrl, ...] = ()
    parser_version: str = Field(min_length=1)
    extraction_kind: ExtractionKind
    metadata: tuple[tuple[str, str], ...] = ()
    dates: tuple[ExtractedDate, ...] = ()
    deadlines: tuple[ExtractedDeadline, ...] = ()
    events: tuple[ExtractedEvent, ...] = ()
    notice_category: NoticeCategory = NoticeCategory.UNKNOWN
    source_relative_id: str = Field(min_length=1)
    quality: ExtractionQuality
