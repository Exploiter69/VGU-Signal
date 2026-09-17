from __future__ import annotations

import fitz

from vgu_signal.extraction import pdf
from vgu_signal.extraction.html import extract_document
from vgu_signal.extraction.models import ExtractionKind, QualityLevel


def make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    body = document.tobytes()
    document.close()
    return body


def test_pdfplumber_crosscheck_disagreement_is_visible(monkeypatch) -> None:
    body = make_pdf("Short extract")
    monkeypatch.setattr(
        pdf, "_extract_pdfplumber", lambda _: "A different longer extraction " * 10
    )
    result = pdf.extract_pdf(
        evidence_id="ev",
        source_id="rules",
        url="https://vgu.ac.in/rules.pdf",
        body=body,
    )
    assert result.body_text.startswith("A different longer extraction")
    assert any("pdfplumber supplied more text" in warning for warning in result.quality.warnings)


def test_pdfplumber_is_fallback_when_primary_extraction_fails(monkeypatch) -> None:
    body = make_pdf("ignored")
    fallback = "Fallback extraction " * 20
    monkeypatch.setattr(
        pdf,
        "_extract_pymupdf",
        lambda _: (_ for _ in ()).throw(RuntimeError("broken")),
    )
    monkeypatch.setattr(pdf, "_extract_pdfplumber", lambda _: fallback)
    monkeypatch.setattr(pdf, "_ocr", lambda _: "")
    result = pdf.extract_pdf(
        evidence_id="ev",
        source_id="rules",
        url="https://vgu.ac.in/rules.pdf",
        body=body,
    )
    assert result.body_text == fallback
    assert result.extraction_kind == ExtractionKind.PDF
    assert result.quality.level == QualityLevel.MEDIUM


def test_sparse_pdf_uses_ocr_and_records_parser_kind(monkeypatch) -> None:
    body = make_pdf("x")
    ocr_text = "OCR recovered exam form deadline on 20 September 2026. " * 5
    monkeypatch.setattr(pdf, "_ocr", lambda _: ocr_text)
    result = pdf.extract_pdf(
        evidence_id="ev",
        source_id="rules",
        url="https://vgu.ac.in/rules.pdf",
        body=body,
    )
    assert result.extraction_kind == ExtractionKind.OCR
    assert result.parser_version == "pdf-ocr-tesseract-v1"
    assert result.deadlines


def test_html_metadata_links_and_script_removal_are_deterministic() -> None:
    html = b"""
    <html>
      <head>
        <title>Exam Notice</title>
        <meta name='description' content='Official notice'>
        <meta property='article:published_time' content='2026-09-20T10:00:00+05:30'>
        <script>alert('ignore')</script>
      </head>
      <body><main>
        <p>Exam form submission closes on 20 September 2026.</p>
        <a href='/notice.pdf'>Rules</a><a href='/notice.pdf'>Duplicate</a>
      </main></body>
    </html>
    """
    result = extract_document(
        evidence_id="ev",
        source_id="notices",
        url="https://vgu.ac.in/notices/today",
        body=html,
    )
    assert result.title == "Exam Notice"
    assert "alert" not in result.body_text
    assert len(result.links) == 1
    assert str(result.links[0]) == "https://vgu.ac.in/notice.pdf"
    assert result.published_at is not None
    assert result.deadlines
