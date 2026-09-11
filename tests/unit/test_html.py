from vgu_signal.extraction.html import PARSER_VERSION, extract_document

FIXTURE = b"""
<html><head><title>Important Notice</title></head>
<body><header>ignore navigation</header><main>
<h1>Important Notice</h1>
<p>Exam form submission closes on 20 September 2026.</p>
<a href="/resources/notice.pdf">Official notice</a>
<script>not part of evidence text</script>
</main></body></html>
"""


def test_html_extraction_is_deterministic() -> None:
    first = extract_document(
        evidence_id="ev-1", source_id="vgu-resources", url="https://vgu.ac.in/resources", body=FIXTURE
    )
    second = extract_document(
        evidence_id="ev-1", source_id="vgu-resources", url="https://vgu.ac.in/resources", body=FIXTURE
    )

    assert first == second
    assert first.title == "Important Notice"
    assert "20 September 2026" in first.body_text
    assert "not part of evidence" not in first.body_text
    assert first.links == ("https://vgu.ac.in/resources/notice.pdf",)
    assert first.parser_version == PARSER_VERSION
