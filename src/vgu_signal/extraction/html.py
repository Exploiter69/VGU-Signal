from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import cast
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl

from vgu_signal.extraction.common import (
    PARSER_VERSION,
    classify_notice,
    extract_dates,
    extract_deadlines,
    extract_events,
    normalize_text,
    source_relative_id,
)
from vgu_signal.extraction.models import (
    ExtractedDocument,
    ExtractionKind,
    ExtractionQuality,
    QualityLevel,
)

_BOILERPLATE_TAGS = {"aside", "footer", "nav"}
_BOILERPLATE_MARKERS = (
    "breadcrumb",
    "cookie",
    "consent",
    "footer",
    "header",
    "menu",
    "modal",
    "navigation",
    "popup",
    "sidebar",
    "social",
    "subscribe",
    "advert",
    "banner",
    "call-to-action",
    "cta",
    "marketing",
    "promotion",
    "quick-links",
    "whatsapp",
)


def _remove_boilerplate(soup: BeautifulSoup) -> None:
    for element in soup(["script", "style", "noscript", "template"]):
        element.decompose()

    for element in soup.find_all(_BOILERPLATE_TAGS):
        element.decompose()

    for element in list(soup.find_all(True)):
        # Earlier decompose() calls can invalidate descendants that are still
        # present in this snapshot. Skip detached/decomposed tags safely.
        if element.parent is None or element.attrs is None:
            continue
        if element.get("aria-hidden") == "true":
            element.decompose()
            continue
        marker_parts: list[str] = []
        for attribute in ("id", "class", "role"):
            value = element.attrs.get(attribute)
            if isinstance(value, list):
                marker_parts.extend(str(item).casefold() for item in value)
            elif value is not None:
                marker_parts.append(str(value).casefold())
        marker = " ".join(marker_parts)
        if any(term in marker for term in _BOILERPLATE_MARKERS):
            element.decompose()
            continue

        if element.name in {"div", "section", "ul", "ol"}:
            text = element.get_text(" ", strip=True)
            links = element.find_all("a")
            linked_text = " ".join(link.get_text(" ", strip=True) for link in links)
            if len(text) >= 40 and len(links) >= 3 and len(linked_text) / max(len(text), 1) >= 0.65:
                element.decompose()


def _content_root(soup: BeautifulSoup) -> Tag:
    main = soup.find("main")
    if main is not None:
        return main
    article = soup.find("article")
    if article is not None:
        return article
    return soup.body or soup


def _document_title(soup: BeautifulSoup, root: Tag) -> str:
    heading = root.find(["h1", "h2"])
    if heading:
        value = heading.get_text(" ", strip=True)
        if value:
            return value
    if soup.title:
        value = soup.title.get_text(" ", strip=True)
        if value:
            return value
    return "Untitled VGU document"


def extract_document(
    *, evidence_id: str, source_id: str, url: str, body: bytes
) -> ExtractedDocument:
    soup = BeautifulSoup(body, "html.parser")
    _remove_boilerplate(soup)

    main = _content_root(soup)
    title = _document_title(soup, main)
    text = normalize_text("\n".join(main.stripped_strings))

    links: list[HttpUrl] = []
    seen_links: set[str] = set()
    for anchor in main.find_all("a"):
        href = anchor.get("href")
        if isinstance(href, str) and href.strip():
            absolute = urljoin(url, href.strip())
            if urlsplit(absolute).scheme.lower() not in {"http", "https"}:
                continue
            if absolute not in seen_links:
                seen_links.add(absolute)
                links.append(cast(HttpUrl, absolute))

    metadata: list[tuple[str, str]] = []
    for tag in soup.find_all("meta"):
        key = tag.get("name") or tag.get("property")
        value = tag.get("content")
        if isinstance(key, str) and isinstance(value, str) and value.strip():
            metadata.append((key.strip().lower(), value.strip()))

    published_at = None
    for key, value in metadata:
        if key in {"article:published_time", "date", "publish-date", "datepublished"}:
            try:
                published_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
            break

    raw_hash = sha256(body).hexdigest()
    document_id = sha256(f"{source_id}:{url}:{raw_hash}:{PARSER_VERSION}".encode()).hexdigest()
    dates = extract_dates(text)
    score = 0.98 if len(text) >= 400 else 0.80 if len(text) >= 100 else 0.45 if text else 0.0
    if score >= 0.9:
        level = QualityLevel.HIGH
    elif score >= 0.7:
        level = QualityLevel.MEDIUM
    elif score:
        level = QualityLevel.LOW
    else:
        level = QualityLevel.FAILED
    quality = ExtractionQuality(
        level=level,
        score=score,
        text_length=len(text),
        page_count=None,
        extraction_kind=ExtractionKind.HTML,
    )
    return ExtractedDocument(
        id=document_id,
        evidence_id=evidence_id,
        source_id=source_id,
        canonical_url=cast(HttpUrl, url),
        title=title,
        published_at=published_at,
        body_text=text,
        links=tuple(links),
        parser_version=PARSER_VERSION,
        extraction_kind=ExtractionKind.HTML,
        metadata=tuple(sorted(metadata)),
        dates=dates,
        deadlines=extract_deadlines(text),
        events=extract_events(text),
        notice_category=classify_notice(text, title),
        source_relative_id=source_relative_id(source_id, url, raw_hash),
        quality=quality,
    )
