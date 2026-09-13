from __future__ import annotations

from types import MappingProxyType

from vgu_signal.domain import Source, SourceClass

VGU_RESOURCES = Source(
    id="vgu-resources",
    name="VGU official resources",
    url="https://vgu.ac.in/resources/handbook-brochures",
    source_class=SourceClass.OFFICIAL,
)

SOURCES = MappingProxyType({VGU_RESOURCES.id: VGU_RESOURCES})


def get_source(source_id: str) -> Source:
    try:
        return SOURCES[source_id]
    except KeyError as exc:
        raise KeyError(f"unknown source: {source_id}") from exc
