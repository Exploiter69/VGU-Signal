from __future__ import annotations

import re
from datetime import datetime
from hashlib import sha256

from vgu_signal.extraction.common import extract_dates, source_relative_id
from vgu_signal.extraction.models import ExtractedDate


class CalendarEntry:
    """Normalized calendar row represented as a small value object."""

    __slots__ = ("id", "label", "start", "end", "source_text", "confidence")

    def __init__(
        self,
        *,
        id: str,
        label: str,
        start: datetime,
        end: datetime | None,
        source_text: str,
        confidence: float,
    ) -> None:
        self.id = id
        self.label = label
        self.start = start
        self.end = end
        self.source_text = source_text
        self.confidence = confidence

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CalendarEntry) and self.as_tuple() == other.as_tuple()

    def __repr__(self) -> str:
        return f"CalendarEntry(label={self.label!r}, start={self.start!r}, end={self.end!r})"

    def as_tuple(self) -> tuple[object, ...]:
        return (self.id, self.label, self.start, self.end, self.source_text, self.confidence)


def _calendar_label(line: str) -> str:
    label = line
    for date in extract_dates(line):
        label = label.replace(date.source_text, " ")
    label = re.sub(r"\b(?:to|through|until)\b", " ", label, flags=re.I)
    label = re.sub(r"\s+", " ", label).strip(" :-|\t–—")
    return label or "Academic calendar entry"


def normalize_academic_calendar(
    *, source_id: str, canonical_url: str, text: str
) -> tuple[CalendarEntry, ...]:
    """Convert common VGU calendar prose/table lines into stable rows.

    Rows without a parseable explicit date are left out rather than guessed.
    """
    entries: list[CalendarEntry] = []
    for line in (part.strip() for part in text.splitlines()):
        if not line:
            continue
        dates = extract_dates(line)
        if not dates:
            continue
        start = dates[0].value
        end = dates[1].value if len(dates) > 1 else None
        label = _calendar_label(line)
        key = f"{start.isoformat()}:{end.isoformat() if end else ''}:{label.lower()}"
        entry_id = source_relative_id(source_id, canonical_url, sha256(key.encode()).hexdigest())
        confidence = 0.94 if len(dates) >= 2 else 0.82
        entries.append(
            CalendarEntry(
                id=entry_id,
                label=label,
                start=start,
                end=end,
                source_text=line,
                confidence=confidence,
            )
        )

    unique: dict[str, CalendarEntry] = {entry.id: entry for entry in entries}
    return tuple(
        sorted(unique.values(), key=lambda entry: (entry.start, entry.label.lower(), entry.id))
    )


def calendar_dates(entries: tuple[CalendarEntry, ...]) -> tuple[ExtractedDate, ...]:
    dates: list[ExtractedDate] = []
    for entry in entries:
        dates.append(
            ExtractedDate(
                value=entry.start,
                label=entry.label,
                source_text=entry.source_text,
                confidence=entry.confidence,
            )
        )
        if entry.end is not None:
            dates.append(
                ExtractedDate(
                    value=entry.end,
                    label=f"{entry.label} end",
                    source_text=entry.source_text,
                    confidence=entry.confidence,
                )
            )
    return tuple(dates)
