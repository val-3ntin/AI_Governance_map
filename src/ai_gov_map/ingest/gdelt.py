"""GDELT DOC 2.0 fallback for AI-governance news (no API key)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import requests

from .http_util import HttpError, get_text
from .models import RegulationRecord
from .normalize import make_record, utc_now_iso

logger = logging.getLogger(__name__)

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

DEFAULT_QUERY = (
    '("AI Act" OR "Artificial Intelligence Act" OR "AI governance" '
    'OR "intelligenza artificiale")'
)

# Hard filter — GDELT is noisy
_KEEP = re.compile(
    r"(AI Act|Artificial Intelligence Act|AI governance|AI regulation|"
    r"intelligenza artificiale|EU AI|OECD\.?AI|Garante|AgID)",
    re.I,
)


def fetch_gdelt(
    *,
    query: str = DEFAULT_QUERY,
    maxrecords: int = 40,
    session: requests.Session | None = None,
    raw_dir: Path | None = None,
) -> list[RegulationRecord]:
    """Fetch recent AI-governance articles from GDELT Doc 2.0 ArtList."""
    fetched_at = utc_now_iso()
    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": str(maxrecords),
        "format": "json",
        "sort": "DateDesc",
    }
    try:
        text, resp = get_text(
            GDELT_DOC_API,
            params=params,
            session=session,
            timeout=60,
            retries=4,
            backoff=3.0,
        )
    except HttpError as exc:
        logger.error("GDELT failed: %s", exc)
        raise

    if raw_dir is not None:
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "gdelt_doc.json").write_text(text, encoding="utf-8")

    # GDELT sometimes returns empty body or HTML on rate limit
    if not text.strip():
        raise HttpError(f"GDELT empty response (HTTP {resp.status_code})")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HttpError(
            f"GDELT non-JSON response (HTTP {resp.status_code}): {text[:120]!r}"
        ) from exc

    articles = payload.get("articles") or []
    records: list[RegulationRecord] = []
    for art in articles:
        title = art.get("title") or ""
        url = art.get("url") or ""
        seendate = art.get("seendate") or ""
        domain = art.get("domain") or ""
        language = art.get("language") or ""
        blob = f"{title} {url}"
        if not _KEEP.search(blob):
            continue
        excerpt = f"GDELT Doc 2.0 · {domain} · lang={language}".strip(" ·")
        records.append(
            make_record(
                source="GDELT",
                title=title,
                url=url,
                jurisdiction="International",
                date=seendate,
                text_excerpt=excerpt,
                fetched_at=fetched_at,
            )
        )
    logger.info("GDELT: %s filtered records from %s articles", len(records), len(articles))
    return records
