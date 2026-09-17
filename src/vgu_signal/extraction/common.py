from __future__ import annotations

import re
from datetime import datetime
from hashlib import sha256
from typing import Final
from urllib.parse import quote

from vgu_signal.extraction.models import (
    ExtractedDate,
    ExtractedDeadline,
    ExtractedEvent,
    NoticeCategory,
)

PARSER_VERSION: Final[str] = "deterministic-v1"

_MONTHS: Final[dict[str, int]] = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
_DATE_RE = re.compile(
    r"\b(?P<day>\d{1,2})[\s./-]+(?P<month>[A-Za-z]{3,9}|\d{1,2})[\s./-]+(?P<year>20\d{2})\b"
)
_ISO_RE = re.compile(r"\b20\d{2}-\d{1,2}-\d{1,2}\b")

_DEADLINE_TERMS = ("deadline", "due", "last date", "closes", "closing date", "submit by", "submission")
_EVENT_TERMS = ("event", "seminar", "workshop", "webinar", "orientation", "fest", "conference", "ceremony")
_CATEGORY_TERMS: tuple[tuple[NoticeCategory, tuple[str, ...]], ...] = (
    (NoticeCategory.EXAMINATION, ("exam", "examination", "semester end", "date sheet", "admit card")),
    (NoticeCategory.FEES, ("fee", "fees", "payment", "tuition", "scholarship fee")),
    (NoticeCategory.REGISTRATION, ("registration", "register", "enrolment", "enrollment", "form submission")),
    (NoticeCategory.HOLIDAY, ("holiday", "holidays", "vacation", "closed")),
    (NoticeCategory.EVENT, _EVENT_TERMS),
    (NoticeCategory.ACADEMIC, ("academic calendar", "semester", "session", "academic year", "classes")),
    (NoticeCategory.GENERAL, ("notice", "circular", "notification", "information")),
)


def normalize_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def source_relative_id(source_id: str, canonical_url: str, stable_key: str) -> str:
    """Create a stable identifier scoped to a source, never a global semantic ID."""
    payload = f"{source_id}\x00{canonical_url}\x00{stable_key}".encode()
    return f"{source_id}:{sha256(payload).hexdigest()[:24]}"


def _parse_date(day: int, month: str, year: int) -> datetime | None:
    if month.isdigit():
        month_number = int(month)
    else:
        month_number = _MONTHS.get(month.lower())
        if month_number is None:
            return None
    try:
        return datetime(year, month_number, day)
    except ValueError:
        return None


def extract_dates(text: str) -> tuple[ExtractedDate, ...]:
    found: list[ExtractedDate] = []
    for match in _DATE_RE.finditer(text):
        value = _parse_date(int(match.group("day")), match.group("month"), int(match.group("year")))
        if value is not None:
            found.append(ExtractedDate(value=value, label="date", source_text=match.group(0), confidence=0.95))
    for match in _ISO_RE.finditer(text):
        try:
            value = datetime.fromisoformat(match.group(0))
        except ValueError:
            continue
        found.append(ExtractedDate(value=value, label="date", source_text=match.group(0), confidence=0.99))
    unique: dict[tuple[datetime, str], ExtractedDate] = {(item.value, item.source_text): item for item in found}
    return tuple(sorted(unique.values(), key=lambda item: (item.value, item.source_text)))


def extract_deadlines(text: str) -> tuple[ExtractedDeadline, ...]:
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    result: list[ExtractedDeadline] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if not any(term in lowered for term in _DEADLINE_TERMS):
            continue
        dates = extract_dates(sentence)
        for date in dates:
            title = re.sub(r"\s+", " ", sentence).strip(" .:-")
            if len(title) > 180:
                title = title[:177].rstrip() + "..."
            result.append(ExtractedDeadline(title=title or "VGU deadline", due_at=date.value, source_text=sentence.strip(), confidence=0.88))
    return tuple(_dedupe_deadlines(result))


def extract_events(text: str) -> tuple[ExtractedEvent, ...]:
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    result: list[ExtractedEvent] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if not any(term in lowered for term in _EVENT_TERMS):
            continue
        dates = extract_dates(sentence)
        if not dates:
            continue
        title = re.sub(r"\s+", " ", sentence).strip(" .:-")
        if len(title) > 180:
            title = title[:177].rstrip() + "..."
        result.append(ExtractedEvent(title=title or "VGU event", starts_at=dates[0].value, source_text=sentence.strip(), confidence=0.84))
    return tuple(_dedupe_events(result))


def classify_notice(text: str, title: str = "") -> NoticeCategory:
    haystack = f"{title} {text}".lower()
    scores = {category: sum(haystack.count(term) for term in terms) for category, terms in _CATEGORY_TERMS}
    category, score = max(scores.items(), key=lambda pair: pair[1])
    return category if score else NoticeCategory.UNKNOWN


def _dedupe_deadlines(items: list[ExtractedDeadline]) -> list[ExtractedDeadline]:
    seen: set[tuple[datetime, str]] = set()
    output: list[ExtractedDeadline] = []
    for item in items:
        key = (item.due_at, item.title)
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output


def _dedupe_events(items: list[ExtractedEvent]) -> list[ExtractedEvent]:
    seen: set[tuple[datetime, str]] = set()
    output: list[ExtractedEvent] = []
    for item in items:
        key = (item.starts_at, item.title)
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output
