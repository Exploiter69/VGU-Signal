from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime, timedelta
from hashlib import sha256

from vgu_signal.information.models import (
    Importance,
    InformationCategory,
    InformationItem,
    StudentScope,
    Urgency,
)
from vgu_signal.verification.engine import publishable
from vgu_signal.verification.models import EvidenceClaim

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_CATEGORY_MAP = {
    "ACADEMIC": InformationCategory.CALENDAR,
    "EXAMINATION": InformationCategory.EXAM,
    "FEES": InformationCategory.FEES,
    "REGISTRATION": InformationCategory.REGISTRATION,
    "EVENT": InformationCategory.EVENT,
    "HOLIDAY": InformationCategory.HOLIDAY,
    "GENERAL": InformationCategory.NOTICE,
    "UNKNOWN": InformationCategory.NOTICE,
}


def normalize_text(value: str) -> str:
    return " ".join(_TOKEN_RE.findall(value.casefold()))


def derive_priority(
    *,
    category: InformationCategory,
    now: datetime,
    due_at: datetime | None = None,
    starts_at: datetime | None = None,
    published_text: str = "",
    changed: bool = False,
    scope: StudentScope | None = None,
) -> tuple[Importance, Urgency]:
    """Derive relevance signals deterministically; truth remains Phase 3's concern."""
    target = due_at or starts_at
    if target is not None:
        delta = target - now
        if delta.total_seconds() < 0:
            urgency = Urgency.OVERDUE
        elif delta <= timedelta(days=2):
            urgency = Urgency.IMMEDIATE
        elif delta <= timedelta(days=7):
            urgency = Urgency.SOON
        else:
            urgency = Urgency.UPCOMING
    else:
        urgency = Urgency.NONE

    text = normalize_text(published_text)
    explicit = {
        "urgent",
        "immediate",
        "last date",
        "final date",
        "important",
        "mandatory",
        "must",
    }
    has_explicit = any(term in text for term in explicit)
    consequence_category = category in {
        InformationCategory.EXAM,
        InformationCategory.FEES,
        InformationCategory.REGISTRATION,
        InformationCategory.DEADLINE,
    }
    if urgency == Urgency.OVERDUE or (urgency == Urgency.IMMEDIATE and consequence_category):
        importance = Importance.CRITICAL
    elif changed or has_explicit or consequence_category:
        importance = Importance.HIGH
    elif scope is not None and scope.specificity() >= 3:
        importance = Importance.HIGH
    elif category in {InformationCategory.NOTICE, InformationCategory.CALENDAR}:
        importance = Importance.NORMAL
    else:
        importance = Importance.LOW
    return importance, urgency


def category_from_notice(value: str) -> InformationCategory:
    try:
        return _CATEGORY_MAP[value.upper()]
    except KeyError as exc:
        raise ValueError(f"unsupported notice category: {value}") from exc


def build_information_item(
    *,
    item_id: str,
    claim_id: str,
    title: str,
    summary: str,
    category: InformationCategory,
    source_url: str,
    source_links: Iterable[str] | None = None,
    audience: StudentScope | None = None,
    published_at: datetime | None = None,
    effective_from: datetime | None = None,
    effective_until: datetime | None = None,
    due_at: datetime | None = None,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    supersedes_item_id: str | None = None,
    changed_from_item_id: str | None = None,
    corrected_item_id: str | None = None,
    now: datetime | None = None,
) -> InformationItem:
    evaluation_time = now or published_at or effective_from or datetime.now()
    importance, urgency = derive_priority(
        category=category,
        now=evaluation_time,
        due_at=due_at,
        starts_at=starts_at,
        published_text=f"{title} {summary}",
        changed=changed_from_item_id is not None or supersedes_item_id is not None,
        scope=audience,
    )
    links = tuple(dict.fromkeys((source_url, *(source_links or ()))))
    from pydantic import HttpUrl

    parsed_links = tuple(HttpUrl(link) for link in links)
    return InformationItem(
        id=item_id,
        claim_id=claim_id,
        title=title.strip(),
        summary=summary.strip(),
        category=category,
        audience=audience or StudentScope(),
        importance=importance,
        urgency=urgency,
        published_at=published_at,
        effective_from=effective_from,
        effective_until=effective_until,
        due_at=due_at,
        starts_at=starts_at,
        ends_at=ends_at,
        source_links=parsed_links,
        primary_source_url=HttpUrl(source_url),
        supersedes_item_id=supersedes_item_id,
        changed_from_item_id=changed_from_item_id,
        corrected_item_id=corrected_item_id,
    )


def _search_score(item: InformationItem, query_tokens: set[str]) -> tuple[int, int, str]:
    if not query_tokens:
        return (0, 0, item.id)
    title_tokens = set(_TOKEN_RE.findall(item.title.casefold()))
    body_tokens = set(_TOKEN_RE.findall(item.summary.casefold()))
    matched_title = len(query_tokens & title_tokens)
    matched_body = len(query_tokens & body_tokens)
    return (matched_title, matched_body, item.id)


def search_archive(
    items: Iterable[InformationItem],
    query: str = "",
    *,
    category: InformationCategory | None = None,
    scope: StudentScope | None = None,
    at: datetime | None = None,
    include_expired: bool = False,
) -> tuple[InformationItem, ...]:
    query_tokens = set(_TOKEN_RE.findall(query.casefold()))
    candidates: list[InformationItem] = []
    for item in items:
        if category is not None and item.category != category:
            continue
        if not item.matches_scope(scope):
            continue
        if at is not None and not include_expired and not item.is_effective_at(at):
            continue
        if query_tokens:
            haystack = set(_TOKEN_RE.findall(f"{item.title} {item.summary}".casefold()))
            if not query_tokens.issubset(haystack):
                continue
        candidates.append(item)

    if at is not None:
        candidates.sort(
            key=lambda item: (
                item.due_at is None,
                item.due_at or item.starts_at or item.effective_from or datetime.max,
                -list(Importance).index(item.importance),
                item.id,
            )
        )
    elif query_tokens:
        candidates.sort(
            key=lambda item: (
                -_search_score(item, query_tokens)[0],
                -_search_score(item, query_tokens)[1],
                -list(Importance).index(item.importance),
                -(item.published_at or datetime.min).timestamp(),
                item.id,
            )
        )
    else:
        candidates.sort(
            key=lambda item: (
                -list(Importance).index(item.importance),
                -(item.published_at or datetime.min).timestamp(),
                item.id,
            )
        )
    return tuple(candidates)


def build_verified_information_item(
    claim: EvidenceClaim,
    *,
    available_evidence_ids: Iterable[str],
    item_id: str,
    title: str,
    summary: str,
    category: InformationCategory,
    source_url: str,
    source_links: Iterable[str] | None = None,
    audience: StudentScope | None = None,
    published_at: datetime | None = None,
    effective_from: datetime | None = None,
    effective_until: datetime | None = None,
    due_at: datetime | None = None,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    supersedes_item_id: str | None = None,
    changed_from_item_id: str | None = None,
    corrected_item_id: str | None = None,
    now: datetime | None = None,
) -> InformationItem:
    if not publishable(claim, available_evidence_ids):
        raise ValueError("information items require a verified claim with traceable evidence")
    return build_information_item(
        item_id=item_id,
        claim_id=claim.id,
        title=title,
        summary=summary,
        category=category,
        source_url=source_url,
        source_links=source_links,
        audience=audience,
        published_at=published_at,
        effective_from=effective_from,
        effective_until=effective_until,
        due_at=due_at,
        starts_at=starts_at,
        ends_at=ends_at,
        supersedes_item_id=supersedes_item_id,
        changed_from_item_id=changed_from_item_id,
        corrected_item_id=corrected_item_id,
        now=now,
    )


def information_item_id(claim_id: str, category: InformationCategory) -> str:
    return f"info:{sha256(f'{claim_id}:{category.value}'.encode()).hexdigest()[:24]}"
