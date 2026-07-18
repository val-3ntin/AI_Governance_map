"""AgID and Garante Privacy RSS adapters."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import feedparser
import requests

from .http_util import HttpError, get_text
from .models import RegulationRecord
from .normalize import make_record, utc_now_iso

logger = logging.getLogger(__name__)

AGID_FEED = "https://www.agid.gov.it/it/rss.xml"
GARANTE_FEED = "https://www.garanteprivacy.it/o/gpdp-rss/rss?t=news"

# Soft keyword filter — keep AI/governance-relevant Italian institutional posts,
# but if nothing matches, keep a small recent sample so the feed still contributes.
_AI_KEYWORDS = re.compile(
    r"\b(ai|ia|intelligenza artificiale|artificial intelligence|algoritm|"
    r"machine learning|data governance|privacy|gdpr|atto|regolament|"
    r"digitale|cyber)\b",
    re.I,
)


def _entry_date(entry: dict) -> str:
    for key in ("published", "updated", "created"):
        val = entry.get(key)
        if val:
            return str(val)
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        try:
            return f"{parsed.tm_year:04d}-{parsed.tm_mon:02d}-{parsed.tm_mday:02d}"
        except (AttributeError, TypeError, ValueError):
            pass
    return ""


def _parse_feed(
    xml_text: str,
    *,
    source: str,
    jurisdiction: str,
    fetched_at: str,
    filter_ai: bool = True,
    max_keep: int = 25,
) -> list[RegulationRecord]:
    parsed = feedparser.parse(xml_text)
    if getattr(parsed, "bozo", False) and not parsed.entries:
        raise HttpError(f"{source} RSS parse failed: {getattr(parsed, 'bozo_exception', '')}")

    tagged: list[tuple[bool, RegulationRecord]] = []
    for entry in parsed.entries:
        title = entry.get("title") or ""
        link = entry.get("link") or entry.get("id") or ""
        summary = entry.get("summary") or entry.get("description") or ""
        blob = f"{title} {summary}"
        rec = make_record(
            source=source,
            title=title,
            url=link,
            jurisdiction=jurisdiction,
            date=_entry_date(entry),
            text_excerpt=summary,
            fetched_at=fetched_at,
        )
        tagged.append((bool(_AI_KEYWORDS.search(blob)), rec))

    if filter_ai:
        hits = [r for hit, r in tagged if hit]
        if hits:
            return hits[:max_keep]
    return [r for _, r in tagged][: min(8, max_keep)]


def fetch_rss_source(
    feed_url: str,
    *,
    source: str,
    jurisdiction: str,
    session: requests.Session | None = None,
    raw_dir: Path | None = None,
    raw_name: str | None = None,
) -> list[RegulationRecord]:
    fetched_at = utc_now_iso()
    text, _resp = get_text(feed_url, session=session, timeout=40, retries=3)
    if raw_dir is not None:
        raw_dir.mkdir(parents=True, exist_ok=True)
        name = raw_name or f"{source.lower().replace(' ', '_')}.xml"
        (raw_dir / name).write_text(text, encoding="utf-8")
    records = _parse_feed(
        text,
        source=source,
        jurisdiction=jurisdiction,
        fetched_at=fetched_at,
    )
    logger.info("%s RSS: %s records from %s", source, len(records), feed_url)
    return records


def fetch_agid(
    *,
    session: requests.Session | None = None,
    raw_dir: Path | None = None,
) -> list[RegulationRecord]:
    return fetch_rss_source(
        AGID_FEED,
        source="AgID",
        jurisdiction="Italy",
        session=session,
        raw_dir=raw_dir,
        raw_name="agid_rss.xml",
    )


def fetch_garante(
    *,
    session: requests.Session | None = None,
    raw_dir: Path | None = None,
) -> list[RegulationRecord]:
    return fetch_rss_source(
        GARANTE_FEED,
        source="Garante",
        jurisdiction="Italy",
        session=session,
        raw_dir=raw_dir,
        raw_name="garante_rss.xml",
    )
