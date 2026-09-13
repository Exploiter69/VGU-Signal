from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

import httpx


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes
    etag: str | None
    last_modified: str | None

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
        user_agent: str = "VGU-Signal/0.1 (+https://github.com/Exploiter69/VGU-Signal)",
    ) -> None:
        self._timeout = httpx.Timeout(timeout_seconds)
        self._max_bytes = max_bytes
        self._headers = {"User-Agent": user_agent}

    def fetch(self, url: str) -> FetchResult:
        try:
            with httpx.Client(
                timeout=self._timeout,
                follow_redirects=True,
                headers=self._headers,
            ) as client:
                with client.stream("GET", url) as response:
                    response.raise_for_status()
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > self._max_bytes:
                            raise FetchError(f"response exceeds {self._max_bytes} byte limit")
                    content_type = response.headers.get("content-type", "application/octet-stream")
                    return FetchResult(
                        url=str(response.url),
                        status_code=response.status_code,
                        content_type=content_type,
                        body=bytes(body),
                        etag=response.headers.get("etag"),
                        last_modified=response.headers.get("last-modified"),
                    )
        except FetchError:
            raise
        except httpx.HTTPError as exc:
            raise FetchError(f"HTTP acquisition failed for {url}: {exc}") from exc
