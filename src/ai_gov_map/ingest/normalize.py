"""Normalisation, dedupe, and CSV I/O for regulation records."""

from __future__ import annotations

import csv
import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse, urlunparse

from .models import SCHEMA_COLUMNS, RegulationRecord

logger = logging.getLogger(__name__)

_WHITESPACE = re.compile(r"\s+")
_HTML_TAG = re.compile(r"<[^>]+>")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_text(value: str | None, *, max_len: int = 800) -> str:
    if not value:
        return ""
    text = _HTML_TAG.sub(" ", value)
    text = _WHITESPACE.sub(" ", text).strip()
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.strip()
    path = parsed.path or "/"
    # Drop trailing slash except for root
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, "", parsed.query, "")
    )


def parse_date(value: str | None) -> str:
    """Best-effort parse to ``YYYY-MM-DD`` (UTC calendar date)."""
    if not value:
        return ""
    raw = value.strip()
    if not raw:
        return ""
    # Already ISO-ish
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return m.group(1)
    # Compact GDELT seendate: 20240715T123000Z
    m = re.match(r"^(\d{4})(\d{2})(\d{2})", raw)
    if m and "T" in raw:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # RFC 2822 / feed dates
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        pass
    return ""


def stable_id(*parts: str, prefix: str = "") -> str:
    """Deterministic short id from stable parts (url / celex / title)."""
    blob = "|".join(p.strip().lower() for p in parts if p and p.strip())
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}" if prefix else digest


def make_record(
    *,
    source: str,
    title: str,
    url: str,
    jurisdiction: str,
    date: str | None = None,
    text_excerpt: str | None = None,
    record_id: str | None = None,
    fetched_at: str | None = None,
) -> RegulationRecord:
    title_c = clean_text(title, max_len=300)
    url_c = normalize_url(url)
    rid = record_id or stable_id(source, url_c or title_c, prefix=f"{source.lower()}:")
    return RegulationRecord(
        id=rid,
        date=parse_date(date) or "",
        title=title_c,
        source=source,
        url=url_c,
        jurisdiction=jurisdiction,
        text_excerpt=clean_text(text_excerpt, max_len=800),
        fetched_at=fetched_at or utc_now_iso(),
    )


def read_csv(path: Path) -> list[RegulationRecord]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    records: list[RegulationRecord] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if not row or not any(row.values()):
                continue
            try:
                records.append(RegulationRecord.from_mapping(row))
            except TypeError:
                logger.warning("Skipping malformed CSV row: %s", row)
    return records


def write_csv(path: Path, records: Iterable[RegulationRecord]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [r.to_dict() for r in records]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(SCHEMA_COLUMNS), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def dedupe_records(records: Iterable[RegulationRecord]) -> list[RegulationRecord]:
    """Keep first occurrence by id, then by normalised URL; stable sort."""
    by_id: dict[str, RegulationRecord] = {}
    url_seen: set[str] = set()
    for rec in records:
        if not rec.id:
            continue
        if rec.id in by_id:
            continue
        if rec.url and rec.url in url_seen:
            continue
        by_id[rec.id] = rec
        if rec.url:
            url_seen.add(rec.url)
    ordered = sorted(
        by_id.values(),
        key=lambda r: (r.date or "9999-99-99", r.source, r.id),
        reverse=False,
    )
    # Newest dates first for readability, still deterministic
    return sorted(
        ordered,
        key=lambda r: (r.date or "", r.source, r.id),
        reverse=True,
    )


def merge_records(
    existing: Iterable[RegulationRecord],
    incoming: Iterable[RegulationRecord],
) -> list[RegulationRecord]:
    """Prefer newer fetched_at for the same id; otherwise keep first."""
    merged: dict[str, RegulationRecord] = {}
    for rec in list(existing) + list(incoming):
        prev = merged.get(rec.id)
        if prev is None:
            merged[rec.id] = rec
            continue
        if (rec.fetched_at or "") >= (prev.fetched_at or ""):
            merged[rec.id] = rec
    # Re-run URL dedupe on values
    return dedupe_records(merged.values())
