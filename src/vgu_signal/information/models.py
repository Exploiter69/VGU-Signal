from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class InformationCategory(StrEnum):
    DEADLINE = "DEADLINE"
    EXAM = "EXAM"
    FEES = "FEES"
    REGISTRATION = "REGISTRATION"
    NOTICE = "NOTICE"
    EVENT = "EVENT"
    HOLIDAY = "HOLIDAY"
    CALENDAR = "CALENDAR"


class Importance(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Urgency(StrEnum):
    NONE = "NONE"
    UPCOMING = "UPCOMING"
    SOON = "SOON"
    IMMEDIATE = "IMMEDIATE"
    OVERDUE = "OVERDUE"


class StudentScope(BaseModel):
    model_config = ConfigDict(frozen=True)

    program: str | None = Field(default=None, min_length=1)
    branch: str | None = Field(default=None, min_length=1)
    year: int | None = Field(default=None, ge=1, le=10)
    semester: int | None = Field(default=None, ge=1, le=20)

    def matches(self, other: "StudentScope") -> bool:
        return all(
            expected is None or actual is None or expected == actual
            for expected, actual in (
                (self.program, other.program),
                (self.branch, other.branch),
                (self.year, other.year),
                (self.semester, other.semester),
            )
        )

    def specificity(self) -> int:
        return sum(
            value is not None
            for value in (self.program, self.branch, self.year, self.semester)
        )


class InformationItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    category: InformationCategory
    audience: StudentScope = StudentScope()
    importance: Importance = Importance.NORMAL
    urgency: Urgency = Urgency.NONE
    published_at: datetime | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    due_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    source_links: tuple[HttpUrl, ...] = Field(min_length=1)
    primary_source_url: HttpUrl
    supersedes_item_id: str | None = None
    changed_from_item_id: str | None = None
    corrected_item_id: str | None = None

    def is_effective_at(self, at: datetime) -> bool:
        if self.effective_from is not None and at < self.effective_from:
            return False
        if self.effective_until is not None and at >= self.effective_until:
            return False
        return True

    def matches_scope(self, scope: StudentScope | None) -> bool:
        return scope is None or self.audience.matches(scope)


class InformationRelationshipKind(StrEnum):
    CHANGED = "CHANGED"
    SUPERSEDES = "SUPERSEDES"
    CORRECTS = "CORRECTS"


class InformationRelationship(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    old_item_id: str = Field(min_length=1)
    new_item_id: str = Field(min_length=1)
    kind: InformationRelationshipKind
    created_at: datetime
    reason: str = Field(min_length=1)


class InformationArchive(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: tuple[InformationItem, ...] = ()

    def add(self, item: InformationItem) -> "InformationArchive":
        if any(existing.id == item.id for existing in self.items):
            raise ValueError(f"duplicate information item id: {item.id}")
        return self.model_copy(update={"items": (*self.items, item)})

    def relationships(self) -> tuple[InformationRelationship, ...]:
        relationships: list[InformationRelationship] = []
        for item in self.items:
            if item.changed_from_item_id:
                relationships.append(
                    InformationRelationship(
                        id=f"change:{item.changed_from_item_id}:{item.id}",
                        old_item_id=item.changed_from_item_id,
                        new_item_id=item.id,
                        kind=InformationRelationshipKind.CHANGED,
                        created_at=item.published_at or item.effective_from or datetime.min,
                        reason="new information item records a changed version",
                    )
                )
            if item.supersedes_item_id:
                relationships.append(
                    InformationRelationship(
                        id=f"supersedes:{item.supersedes_item_id}:{item.id}",
                        old_item_id=item.supersedes_item_id,
                        new_item_id=item.id,
                        kind=InformationRelationshipKind.SUPERSEDES,
                        created_at=item.published_at or item.effective_from or datetime.min,
                        reason="new information item supersedes an earlier item",
                    )
                )
            if item.corrected_item_id:
                relationships.append(
                    InformationRelationship(
                        id=f"corrects:{item.corrected_item_id}:{item.id}",
                        old_item_id=item.corrected_item_id,
                        new_item_id=item.id,
                        kind=InformationRelationshipKind.CORRECTS,
                        created_at=item.published_at or item.effective_from or datetime.min,
                        reason="new information item corrects an earlier item",
                    )
                )
        return tuple(relationships)

    def search(
        self,
        query: str = "",
        *,
        category: InformationCategory | None = None,
        scope: StudentScope | None = None,
        at: datetime | None = None,
        include_expired: bool = False,
    ) -> tuple[InformationItem, ...]:
        from vgu_signal.information.engine import search_archive

        return search_archive(
            self.items,
            query,
            category=category,
            scope=scope,
            at=at,
            include_expired=include_expired,
        )
