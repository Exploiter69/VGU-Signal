from __future__ import annotations

import pytest

from vgu_signal.acquisition.policy import (
    PolicyError,
    RobotsPolicy,
    SitemapPolicy,
    validate_content_type,
)


def test_robots_policy_honours_disallow_and_collects_sitemaps() -> None:
    robots = """User-agent: *\nDisallow: /private\nSitemap: https://example.test/sitemap.xml\n"""

    allowed = RobotsPolicy.from_text(
        source_url="https://example.test/public/page",
        user_agent="VGU-Signal",
        robots_text=robots,
    )
    assert allowed.allowed is True
    assert allowed.sitemaps == ("https://example.test/sitemap.xml",)

    blocked = RobotsPolicy.from_text(
        source_url="https://example.test/private/page",
        user_agent="VGU-Signal",
        robots_text=robots,
    )
    assert blocked.allowed is False
    with pytest.raises(PolicyError, match="disallows"):
        blocked.require_allowed()


def test_sitemap_policy_extracts_unique_http_urls() -> None:
    xml = """<?xml version="1.0"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.test/a</loc></url>
      <url><loc>https://example.test/a</loc></url>
      <url><loc>ftp://example.test/b</loc></url>
    </urlset>
    """
    assert SitemapPolicy.extract_urls(xml) == ("https://example.test/a",)


def test_sitemap_policy_rejects_invalid_xml() -> None:
    with pytest.raises(PolicyError, match="invalid sitemap XML"):
        SitemapPolicy.extract_urls("<broken>")


def test_content_type_validation_ignores_parameters() -> None:
    assert validate_content_type("text/html; charset=utf-8", ("text/html",)) == "text/html"
    with pytest.raises(PolicyError, match="unsupported content type"):
        validate_content_type("image/png", ("text/html",))
