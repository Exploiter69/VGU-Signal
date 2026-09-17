from __future__ import annotations

import fitz

from vgu_signal.extraction.calendar import normalize_academic_calendar
from vgu_signal.extraction.common import (
    classify_notice,
    extract_dates,
    extract_deadlines,
    extract_events,
    source_relative_id,
)
from vgu_signal.extraction.models import ExtractionKind, NoticeCategory, QualityLevel
from vgu_signal.extraction.pdf import extract_pdf
from vgu_signal.extraction.pipeline import extract_evidence


def make_pdf(text: str, *, title: str = "Exam Rules") -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    metadata = document.metadata
    metadata["title"] = title
    document.set_metadata(metadata)
    body = document.tobytes()
    document.close()
    return body


def test_dates_are_deterministic_and_ignore_invalid_dates() -> None:
    dates = extract_dates("Exam on 20 September 2026; invalid 31 February 2026; ISO 2026-10-01.")
    assert [item.source_text for item in dates] == ["20 September 2026", "2026-10-01"]


def test_all_supported_explicit_date_forms_are_parsed() -> None:
    dates = extract_dates("01 January 2026; 02 Jan 2026; 03/03/2026; 04-04-2026; 05.05.2026")
    assert [item.value.strftime("%Y-%m-%d") for item in dates] == [
        "2026-01-01",
        "2026-01-02",
        "2026-03-03",
        "2026-04-04",
        "2026-05-05",
    ]


def test_deadline_extraction_requires_deadline_language() -> None:
    result = extract_deadlines(
        "Exam form submission closes on 20 September 2026. Exam is on 25 September 2026."
    )
    assert len(result) == 1
    assert result[0].due_at.isoformat() == "2026-09-20T00:00:00"
    assert result[0].source_text.startswith("Exam form submission")
    assert result[0].confidence < 1


def test_event_extraction_requires_event_language() -> None:
    result = extract_events("Orientation event will be held on 10 October 2026.")
    assert len(result) == 1
    assert result[0].starts_at.isoformat() == "2026-10-10T00:00:00"
    assert not extract_events("Classes will be held on 10 October 2026.")


def test_notice_classification_covers_every_category_and_unknown() -> None:
    cases = {
        NoticeCategory.ACADEMIC: "Academic calendar for the new semester session",
        NoticeCategory.EXAMINATION: "Examination date sheet and admit card notice",
        NoticeCategory.FEES: "Fee payment and tuition information",
        NoticeCategory.REGISTRATION: "Registration and enrolment form submission",
        NoticeCategory.EVENT: "Campus orientation event",
        NoticeCategory.HOLIDAY: "University holiday and vacation notice",
        NoticeCategory.GENERAL: "General circular notification information",
        NoticeCategory.UNKNOWN: "A completely unrelated sentence",
    }
    for expected, text in cases.items():
        assert classify_notice(text) == expected


def test_source_relative_identifier_is_stable_and_source_scoped() -> None:
    first = source_relative_id("calendar", "https://vgu.ac.in/a.pdf", "row-1")
    assert first == source_relative_id("calendar", "https://vgu.ac.in/a.pdf", "row-1")
    assert first != source_relative_id("other", "https://vgu.ac.in/a.pdf", "row-1")
    assert first != source_relative_id("calendar", "https://vgu.ac.in/b.pdf", "row-1")
    assert first.startswith("calendar:")


def test_pdf_primary_extraction_metadata_and_quality() -> None:
    body = make_pdf(
        "Exam form submission closes on 20 September 2026. "
        "Students must verify the examination registration details before submission. "
        "Late submission may not be accepted by the university examination cell."
    )
    result = extract_pdf(
        evidence_id="ev-pdf",
        source_id="exam-rules",
        url="https://vgu.ac.in/exam-rules.pdf",
        body=body,
    )
    assert result.extraction_kind == ExtractionKind.PDF
    assert result.title == "Exam Rules"
    assert result.deadlines[0].due_at.isoformat() == "2026-09-20T00:00:00"
    assert result.quality.level in {QualityLevel.MEDIUM, QualityLevel.HIGH}
    assert result.quality.page_count == 1
    assert result.evidence_id == "ev-pdf"
    assert result.source_id == "exam-rules"
    assert str(result.canonical_url) == "https://vgu.ac.in/exam-rules.pdf"
    assert result.source_relative_id.startswith("exam-rules:")


def test_pipeline_dispatches_html_and_pdf() -> None:
    html = b"<html><title>Notice</title><main>Exam form closes on 20 September 2026.</main></html>"
    html_result = extract_evidence(
        evidence_id="ev-html",
        source_id="notice",
        url="https://vgu.ac.in/n",
        content_type="text/html; charset=utf-8",
        body=html,
    )
    pdf_result = extract_evidence(
        evidence_id="ev-pdf",
        source_id="notice",
        url="https://vgu.ac.in/n.pdf",
        content_type="application/pdf",
        body=make_pdf("Exam form closes on 20 September 2026."),
    )
    assert html_result.extraction_kind == ExtractionKind.HTML
    assert pdf_result.extraction_kind == ExtractionKind.PDF


def test_text_dispatch_is_deterministic() -> None:
    body = b"Exam form closes on 20 September 2026."
    first = extract_evidence(
        evidence_id="ev-text",
        source_id="notice",
        url="https://vgu.ac.in/notice.txt",
        content_type="text/plain; charset=utf-8",
        body=body,
    )
    second = extract_evidence(
        evidence_id="ev-text",
        source_id="notice",
        url="https://vgu.ac.in/notice.txt",
        content_type="text/plain; charset=utf-8",
        body=body,
    )
    assert first == second
    assert first.extraction_kind == ExtractionKind.TEXT
    assert first.deadlines


def test_unsupported_content_type_fails_closed() -> None:
    try:
        extract_evidence(
            evidence_id="ev",
            source_id="x",
            url="https://vgu.ac.in/x",
            content_type="image/jpeg",
            body=b"x",
        )
    except ValueError as exc:
        assert "unsupported extraction content type" in str(exc)
    else:
        raise AssertionError("unsupported media type must fail closed")


def test_academic_calendar_normalization_is_sorted_and_stable() -> None:
    text = (
        "Orientation: 10 October 2026 to 12 October 2026\n"
        "Mid semester examinations: 20 September 2026\n"
        "Orientation: 10 October 2026 to 12 October 2026\n"
        "No date in this row\n"
    )
    entries = normalize_academic_calendar(
        source_id="calendar",
        canonical_url="https://vgu.ac.in/calendar.pdf",
        text=text,
    )
    assert len(entries) == 2
    assert entries[0].label == "Mid semester examinations"
    assert entries[1].start.isoformat() == "2026-10-10T00:00:00"
    assert entries[1].end is not None
    assert entries[0].confidence < entries[1].confidence
    assert entries == normalize_academic_calendar(
        source_id="calendar",
        canonical_url="https://vgu.ac.in/calendar.pdf",
        text=text,
    )
