from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET


class PolicyError(RuntimeError):
    """Raised when a source cannot be safely acquired under its policy."""


@dataclass(frozen=True)
class RobotsPolicy:
    user_agent: str
    robots_url: str
    allowed: bool
    sitemaps: tuple[str, ...] = ()

    @classmethod
    def from_text(cls, *, source_url: str, user_agent: str, robots_text: str) -> RobotsPolicy:
        parser = RobotFileParser()
        parser.set_url(urljoin(source_url, "/robots.txt"))
        parser.parse(robots_text.splitlines())
        return cls(
            user_agent=user_agent,
            robots_url=parser.url,
            allowed=parser.can_fetch(user_agent, source_url),
            sitemaps=tuple(parser.site_maps()),
        )

    def require_allowed(self) -> None:
        if not self.allowed:
            raise PolicyError(f"robots.txt disallows acquisition of {self.robots_url}")


@dataclass(frozen=True)
class SitemapPolicy:
    sitemap_urls: tuple[str, ...]

    @classmethod
    def from_robots(cls, robots: RobotsPolicy) -> SitemapPolicy:
        return cls(sitemap_urls=robots.sitemaps)

    @staticmethod
    def extract_urls(xml_text: str) -> tuple[str, ...]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise PolicyError("invalid sitemap XML") from exc
        urls: list[str] = []
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] != "loc" or not element.text:
                continue
            value = element.text.strip()
            if value and urlparse(value).scheme in {"http", "https"}:
                urls.append(value)
        return tuple(dict.fromkeys(urls))


def validate_content_type(content_type: str, allowed: tuple[str, ...]) -> str:
    media_type = content_type.split(";", 1)[0].strip().lower()
    normalized = tuple(value.lower() for value in allowed)
    if media_type not in normalized:
        raise PolicyError(f"unsupported content type {media_type!r}; expected one of {normalized}")
    return media_type
