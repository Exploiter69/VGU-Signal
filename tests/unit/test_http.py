from __future__ import annotations

import httpx
import pytest

from vgu_signal.acquisition.http import FetchError, HttpFetcher


def test_fetch_returns_body_hash_and_http_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8", "etag": '"abc"'},
            content=b"hello",
            request=request,
        )

    result = HttpFetcher(transport=httpx.MockTransport(handler)).fetch("https://example.test")

    assert result.status_code == 200
    assert result.content_type == "text/html; charset=utf-8"
    assert result.etag == '"abc"'
    assert (
        result.raw_content_hash
        == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_fetch_sends_conditional_headers_and_accepts_304() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["etag"] = request.headers["if-none-match"]
        seen["modified"] = request.headers["if-modified-since"]
        return httpx.Response(304, headers={"etag": '"abc"'}, request=request)

    result = HttpFetcher(transport=httpx.MockTransport(handler)).fetch(
        "https://example.test",
        etag='"abc"',
        last_modified="Wed, 01 Jan 2025 00:00:00 GMT",
    )

    assert seen == {
        "etag": '"abc"',
        "modified": "Wed, 01 Jan 2025 00:00:00 GMT",
    }
    assert result.not_modified is True
    assert result.status_code == 304
    assert result.body == b""


def test_fetch_retries_transient_status() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200, headers={"content-type": "text/plain"}, content=b"ok", request=request
        )

    sleeps: list[float] = []
    result = HttpFetcher(
        transport=httpx.MockTransport(handler),
        max_retries=1,
        retry_base_seconds=0.25,
        sleep=sleeps.append,
    ).fetch("https://example.test")

    assert attempts == 2
    assert sleeps == [0.25]
    assert result.body == b"ok"


def test_fetch_rejects_oversized_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"012345", request=request)

    with pytest.raises(FetchError, match="exceeds 5"):
        HttpFetcher(
            transport=httpx.MockTransport(handler),
            max_bytes=5,
        ).fetch("https://example.test")


def test_fetch_rejects_non_success_after_retries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, request=request)

    with pytest.raises(FetchError, match="status 404"):
        HttpFetcher(transport=httpx.MockTransport(handler), max_retries=0).fetch(
            "https://example.test"
        )
