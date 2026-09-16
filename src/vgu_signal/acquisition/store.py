from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from vgu_signal.domain import Evidence


class EvidenceStore(Protocol):
    def append(self, evidence: Evidence) -> bool: ...

    def latest(self, source_id: str) -> Evidence | None: ...

    def latest_known_good(self, source_id: str) -> Evidence | None: ...

    def history(self, source_id: str) -> tuple[Evidence, ...]: ...


class InMemoryEvidenceStore:
    """Immutable evidence store used by deterministic tests and local development."""

    def __init__(self, evidence: Iterable[Evidence] = ()) -> None:
        self._items: dict[str, list[Evidence]] = {}
        for item in evidence:
            self.append(item)

    def append(self, evidence: Evidence) -> bool:
        items = self._items.setdefault(evidence.source_id, [])
        if any(item.raw_content_hash == evidence.raw_content_hash for item in items):
            return False
        items.append(evidence)
        items.sort(key=lambda item: item.fetched_at)
        return True

    def latest(self, source_id: str) -> Evidence | None:
        items = self._items.get(source_id, [])
        return items[-1] if items else None

    def latest_known_good(self, source_id: str) -> Evidence | None:
        return self.latest(source_id)

    def history(self, source_id: str) -> tuple[Evidence, ...]:
        return tuple(self._items.get(source_id, ()))
