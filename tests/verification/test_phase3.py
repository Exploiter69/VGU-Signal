from datetime import datetime

import pytest
from pydantic import HttpUrl

from vgu_signal.extraction.models import (
    ExtractedDeadline,
    ExtractedDocument,
    ExtractionKind,
    ExtractionQuality,
    NoticeCategory,
    QualityLevel,
)
from vgu_signal.verification import (
    EvidenceClaim,
    RelationshipKind,
    VerificationState,
    claim_fingerprint,
    claims_from_document,
    conflict_relationship,
    correction_relationship,
    cross_source_similarity,
    deduplicate,
    detect_conflicts,
    detect_url_replacements,
    expiration_state,
    normalize_statement,
    provenance,
    publishable,
    resolve_state,
    same_content_relationships,
    supersession_relationship,
    transition_state,
    verify_claim,
)

NOW = datetime(2026, 9, 17, 12, 0)


def make_document(
    *,
    document_id: str = "doc-1",
    evidence_id: str = "ev-1",
    source_id: str = "vgu-notices",
    url: str = "https://vgu.ac.in/notice.pdf",
    title: str = "Notice",
    body: str = "",
    relative_id: str = "vgu-notices:stable",
) -> ExtractedDocument:
    return ExtractedDocument(
        id=document_id,
        evidence_id=evidence_id,
        source_id=source_id,
        canonical_url=HttpUrl(url),
        title=title,
        body_text=body,
        links=(),
        parser_version="deterministic-v1",
        extraction_kind=ExtractionKind.PDF,
        metadata=(),
        dates=(),
        deadlines=(),
        events=(),
        notice_category=NoticeCategory.GENERAL,
        source_relative_id=relative_id,
        quality=ExtractionQuality(
            level=QualityLevel.HIGH,
            score=0.95,
            text_length=len(body),
            page_count=1,
            extraction_kind=ExtractionKind.PDF,
        ),
    )


def make_claim(
    statement: str,
    *,
    claim_id: str = "claim-1",
    evidence_id: str = "ev-1",
    source_id: str = "vgu",
    state: VerificationState = VerificationState.UNVERIFIED,
    effective_until: datetime | None = None,
) -> EvidenceClaim:
    return EvidenceClaim(
        id=claim_id,
        document_id="doc-1",
        evidence_id=evidence_id,
        source_id=source_id,
        statement=statement,
        normalized_statement=normalize_statement(statement),
        fingerprint=claim_fingerprint(statement),
        state=state,
        first_seen_at=NOW,
        last_seen_at=NOW,
        effective_until=effective_until,
    )


def test_evidence_to_claim_retains_provenance_and_never_verifies_by_extraction():
    deadline = ExtractedDeadline(
        title="Fee deadline",
        due_at=datetime(2026, 9, 25),
        source_text="Fee payment deadline is 25 September 2026.",
        confidence=0.88,
    )
    doc = make_document(evidence_id="ev-42").model_copy(update={"deadlines": (deadline,)})
    claims = claims_from_document(doc, "a" * 64, NOW)
    assert len(claims) == 1
    assert claims[0].evidence_id == "ev-42"
    assert claims[0].source_id == "vgu-notices"
    assert claims[0].state == VerificationState.UNVERIFIED
    with pytest.raises(ValueError):
        claims_from_document(doc, "not-a-hash", NOW)


def test_verification_requires_matching_evidence():
    claim = make_claim("Exam form deadline is 25 September 2026.")
    missing = verify_claim(claim, ["other-evidence"], NOW)
    assert missing.state == VerificationState.UNVERIFIED
    verified = verify_claim(claim, [claim.evidence_id], NOW)
    assert verified.state == VerificationState.VERIFIED
    assert verified.evidence_ids == (claim.evidence_id,)


def test_publish_guard_rejects_unverified_and_missing_evidence():
    claim = make_claim("Registration closes 25 September 2026.")
    assert not publishable(claim, [claim.evidence_id])
    verified = claim.model_copy(update={"state": VerificationState.VERIFIED})
    assert publishable(verified, [verified.evidence_id])
    assert not publishable(verified, [])


def test_same_content_deduplication_and_relationships():
    a = make_claim("Registration closes 25 September 2026.", claim_id="a")
    b = make_claim("Registration closes 25 September 2026.", claim_id="b", evidence_id="ev-2")
    unique = make_claim("Registration closes 30 September 2026.", claim_id="c")
    assert len(deduplicate([a, b, unique])) == 2
    relationships = same_content_relationships([a, b, unique], NOW)
    assert len(relationships) == 1
    assert relationships[0].kind == RelationshipKind.SAME_CONTENT


def test_cross_source_similarity_is_bounded_and_skips_same_source():
    a = make_claim(
        "The last date for examination form submission is 25 September 2026.",
        claim_id="a",
        source_id="a",
    )
    b = make_claim(
        "The last date for examination form submission is 25 September 2026.",
        claim_id="b",
        source_id="b",
        evidence_id="ev-2",
    )
    c = make_claim(
        "Library orientation is scheduled for students.",
        claim_id="c",
        source_id="c",
        evidence_id="ev-3",
    )
    relationships = cross_source_similarity([a, b, c], NOW, threshold=0.8)
    assert len(relationships) == 1
    assert relationships[0].kind == RelationshipKind.SIMILAR
    assert relationships[0].similarity == pytest.approx(1.0)
    with pytest.raises(ValueError):
        cross_source_similarity([a, b], NOW, threshold=0)


def test_conflict_detection_requires_same_source_and_different_content():
    a = make_claim(
        "Examination form submission deadline is 25 September 2026.", claim_id="a", source_id="vgu"
    )
    b = make_claim(
        "Examination form submission deadline is 30 September 2026.",
        claim_id="b",
        source_id="vgu",
        evidence_id="ev-2",
    )
    other_source = b.model_copy(update={"id": "c", "source_id": "other"})
    unrelated = make_claim(
        "Hostel orientation is scheduled in October.",
        claim_id="d",
        source_id="vgu",
        evidence_id="ev-3",
    )
    conflicts = detect_conflicts([a, b, other_source, unrelated], NOW)
    assert len(conflicts) == 1
    assert conflicts[0].kind == RelationshipKind.CONFLICTS
    assert conflicts[0].similarity is not None


def test_url_replacement_detects_same_logical_document_moved_between_urls():
    old = make_document(
        url="https://vgu.ac.in/uploads/notice-old.pdf", relative_id="logical-notice"
    )
    new = make_document(
        url="https://vgu.ac.in/uploads/notice-new.pdf", relative_id="logical-notice"
    )
    assert detect_url_replacements(old, new, NOW)
    same = make_document(
        url="https://vgu.ac.in/uploads/notice-old.pdf", relative_id="logical-notice"
    )
    assert not detect_url_replacements(old, same, NOW)


def test_url_replacement_does_not_cross_source_boundary():
    old = make_document(source_id="source-a", relative_id="logical")
    new = make_document(
        source_id="source-b", relative_id="logical", url="https://vgu.ac.in/new.pdf"
    )
    assert not detect_url_replacements(old, new, NOW)


def test_supersession_correction_and_conflict_relationships_are_explicit():
    old = make_claim(
        "Deadline is 25 September 2026.", claim_id="old", state=VerificationState.VERIFIED
    )
    new = make_claim(
        "Deadline is 30 September 2026.",
        claim_id="new",
        evidence_id="ev-2",
        state=VerificationState.VERIFIED,
    )
    assert supersession_relationship(old, new, NOW).kind == RelationshipKind.SUPERSEDES
    assert correction_relationship(old, new, NOW).kind == RelationshipKind.CORRECTS
    assert conflict_relationship(old, new, NOW).kind == RelationshipKind.CONFLICTS
    assert new.model_copy(update={"supersedes_claim_id": old.id}).supersedes_claim_id == old.id


def test_expiration_is_time_based_and_never_upgrades_unverified_claims():
    expiry = datetime(2026, 9, 17, 11, 59)
    verified = make_claim(
        "Deadline is today.", state=VerificationState.VERIFIED, effective_until=expiry
    )
    assert expiration_state(verified, NOW) == VerificationState.EXPIRED
    unverified = make_claim("Deadline is today.", effective_until=expiry)
    assert expiration_state(unverified, NOW) == VerificationState.EXPIRED
    open_claim = make_claim("Deadline is today.")
    assert expiration_state(open_claim, NOW) == VerificationState.UNVERIFIED


def test_state_machine_allows_only_declared_transitions():
    assert (
        transition_state(VerificationState.UNVERIFIED, VerificationState.VERIFIED)
        == VerificationState.VERIFIED
    )
    assert (
        transition_state(VerificationState.VERIFIED, VerificationState.SUPERSEDED)
        == VerificationState.SUPERSEDED
    )
    assert (
        transition_state(VerificationState.VERIFIED, VerificationState.CONFLICTING)
        == VerificationState.CONFLICTING
    )
    with pytest.raises(ValueError):
        transition_state(VerificationState.SUPERSEDED, VerificationState.VERIFIED)
    with pytest.raises(ValueError):
        transition_state(VerificationState.REMOVED, VerificationState.VERIFIED)


def test_state_resolution_prevents_ambiguous_priority():
    claim = make_claim("Notice")
    assert resolve_state(claim, verified=True) == VerificationState.VERIFIED
    verified = claim.model_copy(update={"state": VerificationState.VERIFIED})
    assert resolve_state(verified, verified=True, expired=True) == VerificationState.EXPIRED
    assert resolve_state(verified, verified=True, superseded=True) == VerificationState.SUPERSEDED
    assert resolve_state(verified, verified=True, conflicting=True) == VerificationState.CONFLICTING
    assert resolve_state(claim, verified=False) == VerificationState.UNVERIFIED


def test_human_readable_provenance_contains_chain():
    claim = make_claim("Exam form deadline is 25 September 2026.", state=VerificationState.VERIFIED)
    record = provenance(claim, evidence_hash="b" * 64, source_url="https://vgu.ac.in/exams")
    summary = record.human_summary()
    assert claim.id in summary
    assert claim.evidence_id in summary
    assert "vgu.ac.in/exams" in summary
    assert "bbbbbbbbbbbb" in summary


def test_claim_fingerprint_is_whitespace_and_case_stable():
    assert claim_fingerprint("Deadline: 25 September 2026") == claim_fingerprint(
        " deadline 25 September 2026 "
    )
