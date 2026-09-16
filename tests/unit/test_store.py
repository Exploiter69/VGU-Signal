from datetime import datetime, timezone

from vgu_signal.acquisition.store import InMemoryEvidenceStore
from vgu_signal.domain import Evidence


def make_evidence(source_id: str, content_hash: str, hour: int) -> Evidence:
    return Evidence(
        id=f"ev-{content_hash}",
        source_id=source_id,
        source_url="https://example.test/source",
        fetched_at=datetime(2026, 9, 16, hour, tzinfo=timezone.utc),
        http_status=200,
        content_type="text/html",
        raw_content_hash=content_hash * 64,
    )


def test_store_is_immutable_and_deduplicates_same_content() -> None:
    store = InMemoryEvidenceStore()
    first = make_evidence("source", "a", 10)
    duplicate = make_evidence("source", "a", 11)
    second = make_evidence("source", "b", 12)

    assert store.append(first) is True
    assert store.append(duplicate) is False
    assert store.append(second) is True
    assert store.latest("source") == second
    assert store.latest_known_good("source") == second
    assert store.history("source") == (first, second)
