"""OECD.AI Policy Observatory comparison source (curated fallback).

OECD.AI does not expose a stable, documented public API for national policy
initiatives (as of Phase 1). This adapter emits a small curated set of
public OECD.AI / EU / Italy policy pages that support EU-vs-Italy comparison
without scraping behind auth or inventing records.
"""

from __future__ import annotations

import logging
from pathlib import Path

import requests

from .http_util import HttpError, get_text
from .models import RegulationRecord
from .normalize import make_record, utc_now_iso

logger = logging.getLogger(__name__)

# Verified public pages (HEAD/GET 200). Update when OECD publishes an open API.
CURATED_ENTRIES: tuple[dict[str, str], ...] = (
    {
        "id": "oecd:italy-national",
        "title": "OECD.AI — Italy national AI policy initiatives",
        "url": "https://oecd.ai/en/dashboards/national/italy",
        "jurisdiction": "Italy",
        "date": "2024-01-01",
        "text_excerpt": (
            "OECD.AI Policy Navigator country view for Italy: national AI strategy, "
            "governance bodies, and policy initiatives (EU vs Italy comparison anchor)."
        ),
    },
    {
        "id": "oecd:eu-overview",
        "title": "OECD.AI — Policy Observatory overview",
        "url": "https://oecd.ai/en/dashboards/overview",
        "jurisdiction": "EU/OECD",
        "date": "2024-01-01",
        "text_excerpt": (
            "OECD.AI Policy Observatory overview — cross-jurisdiction AI policy catalogue "
            "used as the EU/OECD comparison context."
        ),
    },
    {
        "id": "oecd:eu-ai-framework",
        "title": "European approach to artificial intelligence (regulatory framework)",
        "url": "https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai",
        "jurisdiction": "EU",
        "date": "2024-08-01",
        "text_excerpt": (
            "European Commission page on the EU AI Act regulatory framework — "
            "EU-level counterpart to national Italian AI strategy initiatives."
        ),
    },
)


def fetch_oecd_comparison(
    *,
    session: requests.Session | None = None,
    raw_dir: Path | None = None,
    verify_live: bool = True,
) -> list[RegulationRecord]:
    """Return curated OECD/EU/Italy comparison records; optionally ping URLs."""
    fetched_at = utc_now_iso()
    records: list[RegulationRecord] = []
    notes: list[str] = []

    for entry in CURATED_ENTRIES:
        url = entry["url"]
        if verify_live:
            try:
                text, resp = get_text(
                    url,
                    session=session,
                    timeout=30,
                    retries=2,
                    backoff=1.5,
                )
                notes.append(f"{url} -> HTTP {resp.status_code} ({len(text)} bytes)")
            except HttpError as exc:
                logger.warning("OECD curated URL unreachable (%s): %s", url, exc)
                notes.append(f"{url} -> FAIL {exc}")
                # Still keep the catalogue entry; URL is the citation
        records.append(
            make_record(
                source="OECD.AI",
                title=entry["title"],
                url=url,
                jurisdiction=entry["jurisdiction"],
                date=entry.get("date"),
                text_excerpt=entry.get("text_excerpt"),
                record_id=entry["id"],
                fetched_at=fetched_at,
            )
        )

    if raw_dir is not None:
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "oecd_curated_fallback.txt").write_text(
            "OECD.AI has no reliable public API; curated fallback used.\n"
            + "\n".join(notes)
            + "\n",
            encoding="utf-8",
        )

    logger.info("OECD.AI curated fallback: %s records", len(records))
    return records
