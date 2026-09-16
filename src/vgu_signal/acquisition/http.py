from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import time
from email.utils import parsedate_to_datetime
from typing import Callable

import httpx


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes
    etag: str | None
    last_modified: str | None
    not_modified: bool = False

    @property
    def raw_content_hash(self) -> str:
        return sha256(self.body).hexdigest()


class FetchError(RuntimeError):
    """Raised when bounded acquisition cannot produce a valid response."""


class HttpFetcher:
    def __init__(
        self,
        *,
        timeout_seconds: float = 20.0,
        max_bytes: int = 10 * 1024 * 1024,
        max_retries: int = 2,
        retry_base_seconds: float = 0.5,
        min_interval_seconds: float = 0.0,
        user_agent: str = "VGU-Signal/0.1 (+https://github.com/Exploiter69/VGU-Signal)",
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if retry_base_seconds < 0 or min_interval_seconds < 0:
            raise ValueError("retry and rate-limit delays must be non-negative")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._max_bytes = max_bytes
        self._max_retries = max_retries
        self._retry_base_seconds = retry_base_seconds
        self._min_interval_seconds = min_interval_seconds
        self._user_agent = user_agent
        self._headers = {"User-Agent": user_agent}
        self._transport = transport
        self._sleep = sleep
        self._last_request_at: float | None = None

    @property
    def user_agent(self) -> str:
        return self._user_agent

    def fetch(
        self,
        url: str,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> FetchResult:
        headers = dict(self._headers)
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._rate_limit()
            try:
                with httpx.Client(
                    timeout=self._timeout,
                    follow_redirects=True,
                    headers=headers,
                    transport=self._transport,
                ) as client:
                    with client.stream("GET", url) as response:
                        if response.status_code == 304:
                            return FetchResult(
                                url=str(response.url),
                                status_code=304,
                                content_type=response.headers.get("content-type", ""),
                                body=b"",
                                etag=response.headers.get("etag") or etag,
                                last_modified=response.headers.get("last-modified")
                                or last_modified,
                                not_modified=True,
                            )
                        if response.status_code < 200 or response.status_code >= 300:
                            if (
                                self._retryable_status(response.status_code)
                                and attempt < self._max_retries
                            ):
                                self._sleep(self._retry_delay(attempt, response))
                                continue
                            raise FetchError(
                                f"HTTP acquisition returned status {response.status_code} for {url}"
                            )
                        body = bytearray()
                        for chunk in response.iter_bytes():
                            body.extend(chunk)
                            if len(body) > self._max_bytes:
                                raise FetchError(f"response exceeds {self._max_bytes} byte limit")
                        return FetchResult(
                            url=str(response.url),
                            status_code=response.status_code,
                            content_type=response.headers.get(
                                "content-type", "application/octet-stream"
                            ),
                            body=bytes(body),
                            etag=response.headers.get("etag"),
                            last_modified=response.headers.get("last-modified"),
                        )
            except FetchError:
                raise
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    break
                self._sleep(self._retry_base_seconds * (2**attempt))

        detail = f": {last_error}" if last_error else ""
        raise FetchError(f"HTTP acquisition failed for {url}{detail}") from last_error

    def _rate_limit(self) -> None:
        if self._last_request_at is None or self._min_interval_seconds == 0:
            self._last_request_at = time.monotonic()
            return
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._min_interval_seconds:
            self._sleep(self._min_interval_seconds - elapsed)
        self._last_request_at = time.monotonic()

    @staticmethod
    def _retryable_status(status_code: int) -> bool:
        return status_code in {408, 425, 429} or 500 <= status_code <= 599

    def _retry_delay(self, attempt: int, response: httpx.Response) -> float:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(retry_after).timestamp()
                    return max(0.0, retry_at - time.time())
                except (TypeError, ValueError, OverflowError):
                    pass
        return self._retry_base_seconds * (2**attempt)
