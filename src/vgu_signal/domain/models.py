from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TrustState(StrEnum):
    DISCOVERED = "DISCOVERED"
    FETCHED = "FETCHED"
    PARSED = "PARSED"
    VERIFIED = "VERIFIED"
    CHANGED = "CHANGED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"
    REMOVED = "REMOVED"


class SourceClass(StrEnum):
    OFFICIAL = "OFFICIAL"
    COMMUNITY_SIGNAL = "COMMUNITY_SIGNAL"


class VerificationOutcome(StrEnum):
    VERIFIED = "VERIFIED"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"


class Source(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    url: HttpUrl
    source_class: SourceClass = SourceClass.OFFICIAL
    enabled: bool = True
    allowed_content_types: tuple[str, ...] = (
        "text/html",
        "application/xhtml+xml",
        "application/pdf",
        "text/plain",
        "application/xml",
        "text/xml",
    )
    respect_robots: bool = True


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_url: HttpUrl
    fetched_at: datetime
    http_status: int = Field(ge=100, le=599)
    content_type: str = Field(min_length=1)
    raw_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_content_ref: str | None = None
    extracted_text_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    parser_version: str | None = None
    http_last_modified: str | None = None
    http_etag: str | None = None


class Document(BaseModel):
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
    state: TrustState = TrustState.PARSED


class Claim(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    state: TrustState = TrustState.UNVERIFIED
    supersedes_claim_id: str | None = None


class Deadline(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    due_at: datetime


class Event(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime | None = None
