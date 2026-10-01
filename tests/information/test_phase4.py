from datetime import datetime

import pytest

from vgu_signal.information import (
    Importance,
    InformationArchive,
    InformationCategory,
    InformationRelationshipKind,
    StudentScope,
    Urgency,
    build_information_item,
    category_from_notice,
    derive_priority,
    information_item_id,
    search_archive,
)
from vgu_signal.verification import EvidenceClaim, VerificationState

NOW = datetime(2026, 10, 1, 9, 0)


def make_item(
    item_id: str,
    *,
    category: InformationCategory = InformationCategory.NOTICE,
    title: str = "Exam form notice",
    summary: str = "Exam form submission deadline is 5 October 2026.",
    scope: StudentScope | None = None,
    due_at: datetime | None = datetime(2026, 10, 5, 23, 59),
    published_at: datetime | None = datetime(2026, 9, 30, 10, 0),
    effective_until: datetime | None = None,
    changed_from_item_id: str | None = None,
    supersedes_item_id: str | None = None,
    corrected_item_id: str | None = None,
):
    return build_information_item(
        item_id=item_id,
        claim_id=f"claim-{item_id}",
        title=title,
        summary=summary,
        category=category,
        source_url="https://vgu.ac.in/notice.pdf",
        audience=scope,
        due_at=due_at,
        published_at=published_at,
        effective_until=effective_until,
        changed_from_item_id=changed_from_item_id,
        supersedes_item_id=supersedes_item_id,
        corrected_item_id=corrected_item_id,
        now=NOW,
    )


def make_claim(state: VerificationState = VerificationState.VERIFIED) -> EvidenceClaim:
    return EvidenceClaim(
        id="claim-1",
        document_id="doc-1",
        evidence_id="ev-1",
        source_id="vgu",
        statement="Exam form submission deadline is 5 October 2026.",
        normalized_statement="exam form submission deadline is 5 october 2026",
        fingerprint="a" * 64,
        state=state,
        first_seen_at=NOW,
        last_seen_at=NOW,
    )


def test_all_roadmap_categories_are_explicit():
    assert {category.value for category in InformationCategory} == {
        "DEADLINE",
        "EXAM",
        "FEES",
        "REGISTRATION",
        "NOTICE",
        "EVENT",
        "HOLIDAY",
        "CALENDAR",
    }


@pytest.mark.parametrize(
    ("notice", "expected"),
    [
        ("ACADEMIC", InformationCategory.CALENDAR),
        ("EXAMINATION", InformationCategory.EXAM),
        ("FEES", InformationCategory.FEES),
        ("REGISTRATION", InformationCategory.REGISTRATION),
        ("EVENT", InformationCategory.EVENT),
        ("HOLIDAY", InformationCategory.HOLIDAY),
        ("GENERAL", InformationCategory.NOTICE),
        ("UNKNOWN", InformationCategory.NOTICE),
    ],
)
def test_notice_categories_map_deterministically(notice, expected):
    assert category_from_notice(notice) == expected


def test_student_dimensions_are_optional_and_match_wildcards():
    scope = StudentScope(program="B.Tech", branch="CSE", year=2, semester=4)
    exact = StudentScope(program="B.Tech", branch="CSE", year=2, semester=4)
    broader = StudentScope(program="B.Tech", branch="CSE", year=None, semester=None)
    different = StudentScope(program="B.Tech", branch="ECE", year=2, semester=4)
    assert scope.matches(exact)
    assert scope.matches(broader)
    assert not scope.matches(different)
    assert scope.specificity() == 4


def test_priority_model_separates_importance_and_urgency():
    importance, urgency = derive_priority(
        category=InformationCategory.FEES,
        now=NOW,
        due_at=datetime(2026, 10, 2, 9, 0),
    )
    assert importance == Importance.CRITICAL
    assert urgency == Urgency.IMMEDIATE

    importance, urgency = derive_priority(
        category=InformationCategory.EVENT,
        now=NOW,
        starts_at=datetime(2026, 11, 1, 9, 0),
    )
    assert importance == Importance.LOW
    assert urgency == Urgency.UPCOMING


def test_changed_item_is_high_importance_even_without_deadline():
    item = make_item(
        "changed",
        category=InformationCategory.NOTICE,
        due_at=None,
        changed_from_item_id="old",
    )
    assert item.importance == Importance.HIGH


def test_source_links_and_temporal_fields_are_preserved():
    item = make_item(
        "timed",
        published_at=datetime(2026, 9, 28, 12, 0),
        effective_until=datetime(2026, 10, 10, 0, 0),
    ).model_copy(
        update={
            "source_links": (
                "https://vgu.ac.in/notice.pdf",
                "https://vgu.ac.in/notices",
            )
        }
    )
    assert len(item.source_links) == 2
    assert item.primary_source_url == "https://vgu.ac.in/notice.pdf"
    assert item.is_effective_at(datetime(2026, 10, 5))
    assert not item.is_effective_at(datetime(2026, 10, 10))


def test_archive_rejects_duplicate_ids_and_exposes_relationships():
    old = make_item("old", due_at=None)
    new = make_item(
        "new",
        due_at=None,
        changed_from_item_id="old",
        supersedes_item_id="old",
        corrected_item_id="old",
    )
    archive = InformationArchive().add(old).add(new)
    with pytest.raises(ValueError):
        archive.add(new)
    relationships = archive.relationships()
    assert {relationship.kind for relationship in relationships} == {
        InformationRelationshipKind.CHANGED,
        InformationRelationshipKind.SUPERSEDES,
        InformationRelationshipKind.CORRECTS,
    }


def test_search_filters_query_category_scope_and_expiration():
    cse = StudentScope(program="B.Tech", branch="CSE", year=2, semester=4)
    ece = StudentScope(program="B.Tech", branch="ECE", year=2, semester=4)
    archive = (
        InformationArchive()
        .add(make_item("cse", scope=cse))
        .add(
            make_item(
                "ece", scope=ece, title="Holiday notice", summary="Campus holiday on 10 October."
            )
        )
        .add(
            make_item(
                "expired",
                scope=cse,
                due_at=None,
                effective_until=datetime(2026, 9, 30),
            )
        )
    )
    results = archive.search(
        "exam form",
        category=InformationCategory.NOTICE,
        scope=StudentScope(program="B.Tech", branch="CSE"),
        at=NOW,
    )
    assert [item.id for item in results] == ["cse"]
    assert [item.id for item in archive.search("holiday")] == ["ece"]
    assert [item.id for item in archive.search("exam form", at=NOW, include_expired=True)] == [
        "cse",
        "expired",
    ]


def test_search_is_delivery_neutral_and_deterministic():
    items = (
        make_item(
            "low", category=InformationCategory.EVENT, title="Orientation event", summary="Welcome"
        ),
        make_item(
            "high", category=InformationCategory.FEES, title="Fee deadline", summary="Pay fees"
        ),
    )
    first = search_archive(items, at=None)
    second = search_archive(items, at=None)
    assert [item.id for item in first] == [item.id for item in second]
    assert first[0].importance == Importance.HIGH


def test_information_item_id_is_stable():
    assert information_item_id("claim-1", InformationCategory.EXAM) == information_item_id(
        "claim-1", InformationCategory.EXAM
    )
    assert information_item_id("claim-1", InformationCategory.EXAM) != information_item_id(
        "claim-1", InformationCategory.FEES
    )


def test_information_model_can_consume_only_verified_claims():
    from vgu_signal.information.engine import build_verified_information_item

    with pytest.raises(ValueError):
        build_verified_information_item(
            make_claim(VerificationState.UNVERIFIED),
            available_evidence_ids=["ev-1"],
            item_id="info-1",
            title="Exam",
            summary="Exam form deadline.",
            category=InformationCategory.EXAM,
            source_url="https://vgu.ac.in/exam",
            now=NOW,
        )

    item = build_verified_information_item(
        make_claim(),
        available_evidence_ids=["ev-1"],
        item_id="info-1",
        title="Exam",
        summary="Exam form deadline.",
        category=InformationCategory.EXAM,
        source_url="https://vgu.ac.in/exam",
        due_at=datetime(2026, 10, 5),
        now=NOW,
    )
    assert item.claim_id == "claim-1"
    assert item.category == InformationCategory.EXAM
