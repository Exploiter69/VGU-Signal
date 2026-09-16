from __future__ import annotations

from hashlib import sha256
from typing import cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

from vgu_signal.domain import Document

PARSER_VERSION = "html-bs4-v1"


def extract_document(*, evidence_id: str, source_id: str, url: str, body: bytes) -> Document:
    soup = BeautifulSoup(body, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled VGU document"
    main = cast(Tag, soup.find("main") or soup.body or soup)
    text = " ".join(main.stripped_strings)

    links: list[str] = []
    for anchor in main.find_all("a"):
        href = anchor.get("href")
        if isinstance(href, str) and href.strip():
            links.append(urljoin(url, href))

    document_id = sha256(f"{source_id}:{url}:{sha256(body).hexdigest()}".encode()).hexdigest()
    return Document(
        id=document_id,
        evidence_id=evidence_id,
        source_id=source_id,
        canonical_url=url,
        title=title,
        body_text=text,
        links=tuple(links),
        parser_version=PARSER_VERSION,
    )
