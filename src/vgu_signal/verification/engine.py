from __future__ import annotations

import re
from datetime import datetime
from hashlib import sha256
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit

from vgu_signal.extraction.models import ExtractedDocument
from vgu_signal.verification.models import (
    ClaimRelationship,
    EvidenceClaim,
    EvidenceLink,
    Provenance,
    RelationshipKind,
    VerificationDecision,
    VerificationState,
)

_WORD_RE = re.compile(r"[a-z0-9]+")


def normalize_statement(statement: str) -> str:
    return " ".join(_WORD_RE.findall(statement.casefold()))


def claim_fingerprint(statement: str) -> str:
    return sha256(normalize_statement(statement).encode()).hexdigest()


def claim_id(document_id: str, statement: str) -> str:
    return f"claim:{document_id}:{claim_fingerprint(statement)[:24]}"


def relationship_id(left: str, right: str, kind: RelationshipKind) -> str:
    ordered = "\x00".join(sorted((left, right)))
    return f"rel:{sha256(f'{kind.value}\x00{ordered}'.encode()).hexdigest()[:32]}"


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (parts.scheme.casefold(), parts.netloc.casefold(), parts.path or "/", parts.query, "")
    )


def url_identity(url: str) -> str:
    return canonicalize_url(url).rstrip("/")


def token_similarity(left: str, right: str) -> float:
    a = set(_WORD_RE.findall(left.casefold()))
    b = set(_WORD_RE.findall(right.casefold()))
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _relationship(
    left: EvidenceClaim,
    right: EvidenceClaim,
    kind: RelationshipKind,
    now: datetime,
    reason: str,
    similarity: float | None = None,
) -> ClaimRelationship:
    return ClaimRelationship(
        id=relationship_id(left.id, right.id, kind),
        left_claim_id=left.id,
        right_claim_id=right.id,
        kind=kind,
        created_at=now,
        reason=reason,
        similarity=similarity,
    )


def claims_from_document(
    document: ExtractedDocument,
    evidence_hash: str,
    observed_at: datetime,
) -> tuple[EvidenceClaim, ...]:
    """Create evidence-backed candidates. Nothing here marks a claim verified."""
    if not re.fullmatch(r"[0-9a-f]{64}", evidence_hash):
        raise ValueError("evidence_hash must be a lowercase SHA-256 hex digest")
    statements: list[tuple[str, datetime | None, datetime | None]] = []
    for item in document.deadlines:
        statements.append((item.source_text, item.due_at, None))
    for item in document.events:
        statements.append((item.source_text, item.starts_at, item.ends_at))
    if not statements and document.body_text.strip():
        statements.append((document.body_text[:1000], None, None))

    output: list[EvidenceClaim] = []
    for statement, effective_from, effective_until in statements:
        normalized = normalize_statement(statement)
        cid = claim_id(document.id, statement)
        output.append(
            EvidenceClaim(
                id=cid,
                document_id=document.id,
                evidence_id=document.evidence_id,
                source_id=document.source_id,
                statement=statement.strip(),
                normalized_statement=normalized,
                fingerprint=sha256(normalized.encode()).hexdigest(),
                first_seen_at=observed_at,
                last_seen_at=observed_at,
                effective_from=effective_from,
                effective_until=effective_until,
            )
        )
    return tuple(output)


def deduplicate(claims: Iterable[EvidenceClaim]) -> tuple[EvidenceClaim, ...]:
    """Keep the first claim for an identical normalized statement+fingerprint."""
    seen: set[str] = set()
    output: list[EvidenceClaim] = []
    for claim in claims:
        if claim.fingerprint in seen:
            continue
        seen.add(claim.fingerprint)
        output.append(claim)
    return tuple(output)


def same_content_relationships(
    claims: Iterable[EvidenceClaim], now: datetime
) -> tuple[ClaimRelationship, ...]:
    items = list(claims)
    output: list[ClaimRelationship] = []
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            if left.fingerprint == right.fingerprint and left.id != right.id:
                output.append(
                    _relationship(
                        left,
                        right,
                        RelationshipKind.SAME_CONTENT,
                        now,
                        "normalized statement fingerprint is identical",
                        1.0,
                    )
                )
    return tuple(output)


def cross_source_similarity(
    claims: Iterable[EvidenceClaim], now: datetime, threshold: float = 0.80
) -> tuple[ClaimRelationship, ...]:
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    items = list(claims)
    output: list[ClaimRelationship] = []
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            if left.source_id == right.source_id or left.fingerprint == right.fingerprint:
                continue
            similarity = token_similarity(left.statement, right.statement)
            if similarity >= threshold:
                output.append(
                    _relationship(
                        left,
                        right,
                        RelationshipKind.SIMILAR,
                        now,
                        "token-set similarity exceeded deterministic threshold",
                        similarity,
                    )
                )
    return tuple(output)


def detect_conflicts(
    claims: Iterable[EvidenceClaim], now: datetime, threshold: float = 0.65
) -> tuple[ClaimRelationship, ...]:
    """Flag high-overlap, same-source claims that are not identical."""
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    items = list(claims)
    output: list[ClaimRelationship] = []
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            if left.source_id != right.source_id or left.fingerprint == right.fingerprint:
                continue
            similarity = token_similarity(left.statement, right.statement)
            if similarity >= threshold:
                output.append(
                    _relationship(
                        left,
                        right,
                        RelationshipKind.CONFLICTS,
                        now,
                        "same-source claims overlap but have different normalized statements",
                        similarity,
                    )
                )
    return tuple(output)


def detect_url_replacements(old: ExtractedDocument, new: ExtractedDocument, now: datetime) -> bool:
    """Detect a logical source-relative document moving to a different URL."""
    del now
    return (
        old.source_id == new.source_id
        and old.source_relative_id == new.source_relative_id
        and url_identity(str(old.canonical_url)) != url_identity(str(new.canonical_url))
    )


def verify_claim(
    claim: EvidenceClaim, available_evidence_ids: Iterable[str], now: datetime
) -> VerificationDecision:
    evidence = tuple(dict.fromkeys(available_evidence_ids))
    if claim.evidence_id not in evidence:
        return VerificationDecision(
            claim_id=claim.id,
            state=VerificationState.UNVERIFIED,
            evidence_ids=evidence,
            reason="claim does not have a matching available evidence record",
            decided_at=now,
        )
    return VerificationDecision(
        claim_id=claim.id,
        state=VerificationState.VERIFIED,
        evidence_ids=(claim.evidence_id,),
        reason="claim is directly traceable to an available evidence record",
        decided_at=now,
    )


_ALLOWED_TRANSITIONS: dict[VerificationState, frozenset[VerificationState]] = {
    VerificationState.UNVERIFIED: frozenset(
        {VerificationState.VERIFIED, VerificationState.CONFLICTING, VerificationState.REMOVED}
    ),
    VerificationState.VERIFIED: frozenset(
        {
            VerificationState.CONFLICTING,
            VerificationState.SUPERSEDED,
            VerificationState.EXPIRED,
            VerificationState.REMOVED,
        }
    ),
    VerificationState.CONFLICTING: frozenset(
        {
            VerificationState.VERIFIED,
            VerificationState.SUPERSEDED,
            VerificationState.EXPIRED,
            VerificationState.REMOVED,
        }
    ),
    VerificationState.SUPERSEDED: frozenset(),
    VerificationState.EXPIRED: frozenset({VerificationState.VERIFIED, VerificationState.REMOVED}),
    VerificationState.REMOVED: frozenset(),
}


def transition_state(current: VerificationState, target: VerificationState) -> VerificationState:
    if target == current:
        return current
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"illegal verification transition: {current.value} -> {target.value}")
    return target


def resolve_state(
    claim: EvidenceClaim,
    *,
    verified: bool,
    conflicting: bool = False,
    expired: bool = False,
    superseded: bool = False,
) -> VerificationState:
    if conflicting:
        target = VerificationState.CONFLICTING
    elif superseded:
        target = VerificationState.SUPERSEDED
    elif expired:
        target = VerificationState.EXPIRED
    else:
        target = VerificationState.VERIFIED if verified else VerificationState.UNVERIFIED
    return transition_state(claim.state, target)


def provenance(
    claim: EvidenceClaim,
    *,
    evidence_hash: str,
    source_url: str,
) -> Provenance:
    return Provenance(
        claim_id=claim.id,
        state=claim.state,
        source_id=claim.source_id,
        source_url=source_url,
        evidence_id=claim.evidence_id,
        document_id=claim.document_id,
        evidence_hash=evidence_hash,
        observed_at=claim.last_seen_at,
        effective_from=claim.effective_from,
        effective_until=claim.effective_until,
        supersedes_claim_id=claim.supersedes_claim_id,
        correction_of_claim_id=claim.correction_of_claim_id,
    )


def publishable(claim: EvidenceClaim, evidence_ids: Iterable[str]) -> bool:
    """The single publication guard for notices/deadlines/events."""
    return claim.state == VerificationState.VERIFIED and claim.evidence_id in set(evidence_ids)


def correction_relationship(
    corrected: EvidenceClaim, correction: EvidenceClaim, now: datetime
) -> ClaimRelationship:
    return _relationship(
        corrected,
        correction,
        RelationshipKind.CORRECTS,
        now,
        "new claim explicitly corrects an earlier claim",
    )


def supersession_relationship(
    old: EvidenceClaim, new: EvidenceClaim, now: datetime
) -> ClaimRelationship:
    return _relationship(
        old,
        new,
        RelationshipKind.SUPERSEDES,
        now,
        "new claim supersedes the earlier claim",
    )


def conflict_relationship(
    left: EvidenceClaim, right: EvidenceClaim, now: datetime
) -> ClaimRelationship:
    return _relationship(
        left,
        right,
        RelationshipKind.CONFLICTS,
        now,
        "claims describe the same logical subject with incompatible statements",
    )


def expiration_state(claim: EvidenceClaim, at: datetime) -> VerificationState:
    if claim.effective_until is not None and at >= claim.effective_until:
        return VerificationState.EXPIRED
    return claim.state


def evidence_link(claim: EvidenceClaim, source_url: str) -> EvidenceLink:
    return EvidenceLink(
        claim_id=claim.id,
        evidence_id=claim.evidence_id,
        source_id=claim.source_id,
        source_url=source_url,
        role="primary evidence",
    )
