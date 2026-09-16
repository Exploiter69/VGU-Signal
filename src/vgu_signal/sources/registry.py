from __future__ import annotations

from types import MappingProxyType
from typing import cast

from pydantic import HttpUrl

from vgu_signal.domain import Source, SourceClass

_DEFAULT_TYPES = (
    "text/html",
    "application/xhtml+xml",
    "application/pdf",
    "text/plain",
    "application/xml",
    "text/xml",
)

VGU_RESOURCES = Source(
    id="vgu-resources",
    name="VGU official resources / handbooks / calendars",
    url=cast(HttpUrl, "https://vgu.ac.in/resources/handbook-brochures"),
    source_class=SourceClass.OFFICIAL,
    allowed_content_types=_DEFAULT_TYPES,
)

VGU_EXAMINATION_RULES = Source(
    id="vgu-examination-rules",
    name="VGU examination rules",
    url=cast(HttpUrl, "https://vgu.ac.in/assets/documents/footer/ExamRules.pdf"),
    source_class=SourceClass.OFFICIAL,
    allowed_content_types=("application/pdf",),
)

VGU_PUBLIC_NOTICE = Source(
    id="vgu-public-notice",
    name="VGU public notice",
    url=cast(HttpUrl, "https://www.vgu.ac.in/PUBLIC-NOTICE-FOR-CDOE.pdf"),
    source_class=SourceClass.OFFICIAL,
    allowed_content_types=("application/pdf",),
)

VGU_FEES = Source(
    id="vgu-fees",
    name="VGU public fee information",
    url=cast(HttpUrl, "https://vgu.ac.in/admission/fee-structure"),
    source_class=SourceClass.OFFICIAL,
    allowed_content_types=("text/html", "application/xhtml+xml"),
)

VGU_EVENTS = Source(
    id="vgu-events",
    name="VGU public events",
    url=cast(HttpUrl, "https://vgu.ac.in/campus-life/events"),
    source_class=SourceClass.OFFICIAL,
    allowed_content_types=("text/html", "application/xhtml+xml"),
)

SOURCES = MappingProxyType(
    {
        source.id: source
        for source in (
            VGU_RESOURCES,
            VGU_EXAMINATION_RULES,
            VGU_PUBLIC_NOTICE,
            VGU_FEES,
            VGU_EVENTS,
        )
    }
)


def get_source(source_id: str) -> Source:
    try:
        return SOURCES[source_id]
    except KeyError as exc:
        raise KeyError(f"unknown source: {source_id}") from exc
