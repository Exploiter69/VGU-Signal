from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Callable
from urllib.parse import urljoin

from vgu_signal.acquisition.http import FetchError, HttpFetcher
from vgu_signal.acquisition.policy import PolicyError, RobotsPolicy, validate_content_type
from vgu_signal.acquisition.store import EvidenceStore
from vgu_signal.domain import Evidence, Source


class AcquisitionStatus(StrEnum):
    FETCHED = "FETCHED"
    UNCHANGED = "UNCHANGED"
    CHANGED = "CHANGED"
    FAILED = "FAILED"


class AcquisitionError(RuntimeError):
    """Raised only for programming/configuration errors in the acquisition engine."""


class AcquisitionResult:
    def __init__(
        self,
        *,
        source_id: str,
        status: AcquisitionStatus,
        evidence: Evidence | None,
        previous_evidence: Evidence | None,
        last_known_good: Evidence | None,
        error: str | None = None,
    ) -> None:
        self.source_id = source_id
        self.status = status
        self.evidence = evidence
        self.previous_evidence = previous_evidence
        self.last_known_good = last_known_good
        self.error = error


class AcquisitionEngine:
    def __init__(
        self,
        fetcher: HttpFetcher,
        store: EvidenceStore,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._fetcher = fetcher
        self._store = store
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def acquire(self, source: Source) -> AcquisitionResult:
        previous = self._store.latest(source.id)
        try:
            self._check_robots(source)
            response = self._fetcher.fetch(
                str(source.url),
                etag=previous.http_etag if previous else None,
                last_modified=previous.http_last_modified if previous else None,
            )
            if response.not_modified:
                if previous is None:
                    raise FetchError("server returned 304 but no previous evidence exists")
                return AcquisitionResult(
                    source_id=source.id,
                    status=AcquisitionStatus.UNCHANGED,
                    evidence=previous,
                    previous_evidence=previous,
                    last_known_good=previous,
                )
            content_type = validate_content_type(
                response.content_type, source.allowed_content_types
            )
            evidence = Evidence(
                id=self._evidence_id(source.id, response.raw_content_hash),
                source_id=source.id,
                source_url=source.url,
                fetched_at=self._clock(),
                http_status=response.status_code,
                content_type=content_type,
                raw_content_hash=response.raw_content_hash,
                raw_content_ref=None,
                extracted_text_hash=None,
                parser_version=None,
                http_last_modified=response.last_modified,
                http_etag=response.etag,
            )
            inserted = self._store.append(evidence)
            if previous is not None and previous.raw_content_hash == evidence.raw_content_hash:
                status = AcquisitionStatus.UNCHANGED
            elif previous is None or inserted:
                status = (
                    AcquisitionStatus.FETCHED if previous is None else AcquisitionStatus.CHANGED
                )
            else:
                status = AcquisitionStatus.UNCHANGED
            return AcquisitionResult(
                source_id=source.id,
                status=status,
                evidence=evidence,
                previous_evidence=previous,
                last_known_good=evidence,
            )
        except (FetchError, PolicyError) as exc:
            return AcquisitionResult(
                source_id=source.id,
                status=AcquisitionStatus.FAILED,
                evidence=None,
                previous_evidence=previous,
                last_known_good=previous,
                error=str(exc),
            )

    def _check_robots(self, source: Source) -> None:
        if not source.respect_robots:
            return
        robots_url = urljoin(str(source.url), "/robots.txt")
        response = self._fetcher.fetch(robots_url)
        if response.status_code < 200 or response.status_code >= 300:
            raise PolicyError(f"robots.txt returned status {response.status_code}")
        policy = RobotsPolicy.from_text(
            source_url=str(source.url),
            user_agent=self._fetcher.user_agent,
            robots_text=response.body.decode("utf-8", errors="replace"),
        )
        policy.require_allowed()

    @staticmethod
    def _evidence_id(source_id: str, content_hash: str) -> str:
        return sha256(f"{source_id}:{content_hash}".encode()).hexdigest()
