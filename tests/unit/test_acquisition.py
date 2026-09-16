from __future__ import annotations

from datetime import datetime, timezone

import httpx

from vgu_signal.acquisition.engine import AcquisitionEngine, AcquisitionStatus
from vgu_signal.acquisition.http import HttpFetcher
from vgu_signal.acquisition.store import InMemoryEvidenceStore
from vgu_signal.domain import Source, SourceClass

SOURCE = Source(
    id="fixture-source",
    name="Fixture source",
    url="https://example.test/source",
    source_class=SourceClass.OFFICIAL,
    respect_robots=False,
    allowed_content_types=("text/html",),
)


def test_engine_fetches_then_detects_unchanged_content() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, headers={"content-type": "text/html"}, content=b"same", request=request)

    store = InMemoryEvidenceStore()
    engine = AcquisitionEngine(
        HttpFetcher(transport=httpx.MockTransport(handler)),
        store,
        clock=lambda: datetime(2026, 9, 16, tzinfo=timezone.utc),
    )

    first = engine.acquire(SOURCE)
    second = engine.acquire(SOURCE)

    assert first.status == AcquisitionStatus.FETCHED
    assert second.status == AcquisitionStatus.UNCHANGED
    assert first.evidence is not None
    assert second.evidence is not None
    assert first.evidence.id == second.evidence.id
    assert len(store.history(SOURCE.id)) == 1
    assert calls == 2


def test_engine_preserves_history_when_content_changes() -> None:
    bodies = iter((b"one", b"two"))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "text/html"}, content=next(bodies), request=request)

    times = iter(
        (
            datetime(2026, 9, 16, 10, tzinfo=timezone.utc),
            datetime(2026, 9, 16, 11, tzinfo=timezone.utc),
        )
    )
    store = InMemoryEvidenceStore()
    engine = AcquisitionEngine(
        HttpFetcher(transport=httpx.MockTransport(handler)),
        store,
        clock=lambda: next(times),
    )

    first = engine.acquire(SOURCE)
    second = engine.acquire(SOURCE)

    assert first.status == AcquisitionStatus.FETCHED
    assert second.status == AcquisitionStatus.CHANGED
    assert first.evidence is not None and second.evidence is not None
    assert first.evidence.id != second.evidence.id
    assert [item.raw_content_hash for item in store.history(SOURCE.id)] == [
        first.evidence.raw_content_hash,
        second.evidence.raw_content_hash,
    ]


def test_engine_uses_last_known_good_after_fetch_failure() -> None:
    responses = iter(
        (
            httpx.Response(200, headers={"content-type": "text/html"}, content=b"known", request=httpx.Request("GET", SOURCE.url)),
            httpx.Response(503, request=httpx.Request("GET", SOURCE.url)),
        )
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    store = InMemoryEvidenceStore()
    engine = AcquisitionEngine(
        HttpFetcher(transport=httpx.MockTransport(handler), max_retries=0),
        store,
    )

    first = engine.acquire(SOURCE)
    failed = engine.acquire(SOURCE)

    assert first.evidence is not None
    assert failed.status == AcquisitionStatus.FAILED
    assert failed.evidence is None
    assert failed.last_known_good == first.evidence
    assert store.latest(SOURCE.id) == first.evidence


def test_engine_checks_robots_before_acquisition() -> None:
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(
                200,
                headers={"content-type": "text/plain"},
                content=b"User-agent: *\nDisallow: /source\n",
                request=request,
            )
        return httpx.Response(200, headers={"content-type": "text/html"}, content=b"blocked", request=request)

    source = SOURCE.model_copy(update={"respect_robots": True})
    result = AcquisitionEngine(
        HttpFetcher(transport=httpx.MockTransport(handler)),
        InMemoryEvidenceStore(),
    ).acquire(source)

    assert result.status == AcquisitionStatus.FAILED
    assert "disallows" in (result.error or "")
    assert requested == ["https://example.test/robots.txt"]
