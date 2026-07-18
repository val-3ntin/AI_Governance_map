"""Heuristics that decide whether a summary needs human review."""

from __future__ import annotations

import re
from typing import Any, Mapping

from ai_gov_map.summarise.models import RISK_TIERS

# Word-boundary hedging / uncertainty cues in summary or rationale text.
HEDGING_PHRASES: tuple[str, ...] = (
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\bpossibly\b",
    r"\bperhaps\b",
    r"\bunclear\b",
    r"\buncertain\b",
    r"\bappears?\b",
    r"\bseems?\b",
    r"\ballegedly\b",
    r"\bpresumably\b",
    r"\broughly\b",
    r"\bapproximately\b",
    r"\bit is possible\b",
    r"\bnot (?:entirely )?clear\b",
    r"\bhard to (?:tell|say|determine)\b",
    r"\bconflicting\b",
    r"\bambiguous\b",
)

_HEDGE_RE = re.compile("|".join(HEDGING_PHRASES), re.IGNORECASE)

# Explicit date-ambiguity language.
_DATE_AMBIGUITY_RE = re.compile(
    r"\b(?:conflicting dates?|date(?:s)? (?:unclear|unknown|ambiguous|uncertain)|"
    r"undated|no (?:clear )?date|date conflict)\b",
    re.IGNORECASE,
)

_YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")
_ISO_DATE_RE = re.compile(r"\b((?:19|20)\d{2})-(\d{2})-(\d{2})\b")

# Default: backend confidence below this triggers review.
LOW_CONFIDENCE_THRESHOLD = 0.5

# Year mismatch between metadata and prose beyond this span is flagged.
YEAR_CONFLICT_SPAN = 2


def _as_mapping(record: Any) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return dict(record)
    if hasattr(record, "to_dict"):
        return dict(record.to_dict())
    return {
        "id": getattr(record, "id", ""),
        "summary": getattr(record, "summary", ""),
        "risk_tier": getattr(record, "risk_tier", ""),
        "rationale": getattr(record, "rationale", ""),
        "confidence": getattr(record, "confidence", 0.5),
        "needs_review": getattr(record, "needs_review", False),
    }


def _blob(row: Mapping[str, Any]) -> str:
    return f"{row.get('summary') or ''}\n{row.get('rationale') or ''}"


def detect_hedging(text: str) -> list[str]:
    """Return human-readable reason strings for hedging matches in ``text``."""
    if not text or not text.strip():
        return []
    hits = sorted({m.group(0).lower() for m in _HEDGE_RE.finditer(text)})
    if not hits:
        return []
    shown = ", ".join(repr(h) for h in hits[:5])
    return [f"hedging language: {shown}"]


def _years_in_text(text: str) -> set[int]:
    years: set[int] = set()
    for m in _YEAR_RE.finditer(text or ""):
        years.add(int(m.group(1)))
    return years


def _metadata_year(metadata_date: str | None) -> int | None:
    if not metadata_date:
        return None
    m = _ISO_DATE_RE.search(str(metadata_date).strip())
    if m:
        return int(m.group(1))
    ym = re.match(r"^((?:19|20)\d{2})", str(metadata_date).strip())
    if ym:
        return int(ym.group(1))
    return None


def detect_date_conflicts(text: str, metadata_date: str | None = None) -> list[str]:
    """Flag ambiguous date language or conflicting years vs metadata / within prose."""
    reasons: list[str] = []
    blob = text or ""
    if _DATE_AMBIGUITY_RE.search(blob):
        reasons.append("ambiguous or conflicting date language in summary/rationale")

    years = _years_in_text(blob)
    if len(years) >= 2 and (max(years) - min(years)) >= YEAR_CONFLICT_SPAN:
        reasons.append(
            f"conflicting years in text: {sorted(years)} (span ≥ {YEAR_CONFLICT_SPAN})"
        )

    meta_year = _metadata_year(metadata_date)
    if meta_year is not None and years:
        distant = [y for y in years if abs(y - meta_year) >= YEAR_CONFLICT_SPAN]
        if distant:
            reasons.append(
                f"summary years {sorted(set(distant))} conflict with metadata year {meta_year}"
            )
    return reasons


def detect_off_taxonomy(risk_tier: str | None) -> list[str]:
    """Flag empty or out-of-taxonomy risk tiers."""
    tier = (risk_tier or "").strip().lower()
    if not tier:
        return ["risk_tier is empty"]
    if tier not in RISK_TIERS:
        return [f"risk_tier {risk_tier!r} outside taxonomy {list(RISK_TIERS)}"]
    return []


def detect_low_confidence(
    confidence: float | None,
    *,
    threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> list[str]:
    try:
        conf = float(confidence) if confidence is not None else 0.0
    except (TypeError, ValueError):
        return ["confidence missing or non-numeric"]
    if conf < threshold:
        return [f"low backend confidence ({conf:.2f} < {threshold:.2f})"]
    return []


def evaluate_summary(
    record: Any,
    *,
    metadata_date: str | None = None,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    """Evaluate a summary record for human review.

    Parameters
    ----------
    record:
        ``SummaryRecord``, mapping, or object with summary fields.
    metadata_date:
        Optional regulation ``date`` (YYYY-MM-DD) for year-conflict checks.

    Returns
    -------
    dict
        ``{"needs_human_review": bool, "reasons": list[str]}``
    """
    row = _as_mapping(record)
    text = _blob(row)
    reasons: list[str] = []
    reasons.extend(detect_hedging(text))
    reasons.extend(detect_date_conflicts(text, metadata_date=metadata_date))
    reasons.extend(detect_off_taxonomy(str(row.get("risk_tier") or "")))
    reasons.extend(
        detect_low_confidence(
            row.get("confidence"),
            threshold=low_confidence_threshold,
        )
    )

    # Preserve an existing backend/offline review flag as an explicit reason.
    existing = row.get("needs_review", False)
    if isinstance(existing, str):
        existing = existing.strip().lower() in {"1", "true", "yes", "y"}
    if existing and not reasons:
        reasons.append("backend already flagged needs_review")

    needs = bool(reasons) or bool(existing)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique.append(r)

    return {
        "needs_human_review": needs,
        "reasons": unique,
    }
