"""Deterministic keyword + taxonomy matcher (no ML)."""

from __future__ import annotations

import re
from typing import Iterable

from ai_gov_map.ingest.models import RegulationRecord

from .models import Entity, ImpactFlag
from .taxonomy import RISK_ALIGNMENT_BOOST, SECTOR_TERMS, USE_CASE_TERMS

# Minimum score to emit a flag (one keyword or taxonomy hit).
MIN_SCORE = 1.0

# Weights
W_KEYWORD = 1.0
W_USE_CASE = 0.75
W_SECTOR = 0.35


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _haystack(record: RegulationRecord) -> str:
    return _norm(f"{record.title} {record.text_excerpt}")


def _term_present(haystack: str, term: str) -> bool:
    """Case-insensitive substring match with light word-boundary for short tokens."""
    t = _norm(term)
    if not t or not haystack:
        return False
    # Short alphanumeric tokens (e.g. "hr", "pa") — require word boundary.
    if len(t) <= 3 and re.fullmatch(r"[a-z0-9]+", t):
        return re.search(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])", haystack) is not None
    return t in haystack


def _collect_hits(haystack: str, terms: Iterable[str]) -> list[str]:
    hits: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = _norm(term)
        if not key or key in seen:
            continue
        if _term_present(haystack, term):
            seen.add(key)
            hits.append(key)
    return hits


def score_match(
    entity: Entity,
    record: RegulationRecord,
    *,
    risk_tier: str = "",
) -> tuple[float, list[str], str]:
    """Return ``(score, matched_terms, reason)`` for one entity × regulation.

    Score is deterministic for fixed inputs. Empty haystack / empty entity
    terms yield ``(0.0, [], …)``.
    """
    haystack = _haystack(record)
    if not haystack:
        return 0.0, [], "empty regulation text"

    kw_hits = _collect_hits(haystack, entity.keywords)
    uc_terms: list[str] = []
    for use_case in entity.ai_use_cases:
        uc_terms.extend(USE_CASE_TERMS.get(use_case, (use_case.replace("_", " "),)))
    uc_hits = _collect_hits(haystack, uc_terms)
    # Avoid double-counting terms already credited as keywords.
    uc_only = [t for t in uc_hits if t not in set(kw_hits)]

    sector_terms = SECTOR_TERMS.get(entity.sector, (entity.sector.replace("_", " "),))
    sec_hits = _collect_hits(haystack, sector_terms)
    already = set(kw_hits) | set(uc_only)
    sec_only = [t for t in sec_hits if t not in already]

    score = (
        W_KEYWORD * len(kw_hits)
        + W_USE_CASE * len(uc_only)
        + W_SECTOR * len(sec_only)
    )

    tier = (risk_tier or "").strip().lower()
    exposure = (entity.risk_exposure or "").strip().lower()
    if tier and exposure and tier == exposure and tier in RISK_ALIGNMENT_BOOST:
        score += RISK_ALIGNMENT_BOOST[tier]

    matched = kw_hits + uc_only + sec_only
    # Stable term order already from entity definition order; sort for CSV stability
    # when sources differ — keep discovery order for readability, then unique.
    parts: list[str] = []
    if kw_hits:
        parts.append(f"keywords={','.join(kw_hits)}")
    if uc_only:
        parts.append(f"use_cases={','.join(uc_only)}")
    if sec_only:
        parts.append(f"sector={','.join(sec_only)}")
    if tier and exposure and tier == exposure and score >= MIN_SCORE:
        parts.append(f"risk_align={tier}")
    reason = "; ".join(parts) if parts else "no overlap"

    return score, matched, reason


def match_pair(
    entity: Entity,
    record: RegulationRecord,
    *,
    risk_tier: str = "",
    flagged_at: str = "",
    min_score: float = MIN_SCORE,
) -> ImpactFlag | None:
    """Return an impact flag if score ≥ ``min_score``, else ``None``."""
    if not entity.id or not record.id:
        return None
    score, matched, reason = score_match(entity, record, risk_tier=risk_tier)
    if score < min_score:
        return None
    ts = flagged_at or record.fetched_at or record.date or ""
    return ImpactFlag(
        regulation_id=record.id,
        entity_id=entity.id,
        match_score=round(score, 2),
        matched_terms="|".join(matched),
        risk_tier=(risk_tier or "").strip().lower(),
        reason=reason,
        flagged_at=ts,
    )


def match_all(
    entities: list[Entity],
    regulations: list[RegulationRecord],
    *,
    risk_tiers: dict[str, str] | None = None,
    flagged_at: str | None = None,
    min_score: float = MIN_SCORE,
) -> list[ImpactFlag]:
    """Match every entity against every regulation; sorted for stable CSV."""
    tiers = risk_tiers or {}
    flags: list[ImpactFlag] = []
    for record in regulations:
        if not record.id:
            continue
        tier = tiers.get(record.id, "")
        for entity in entities:
            if not entity.id:
                continue
            flag = match_pair(
                entity,
                record,
                risk_tier=tier,
                flagged_at=flagged_at if flagged_at is not None else "",
                min_score=min_score,
            )
            if flag is not None:
                flags.append(flag)
    flags.sort(key=lambda f: (f.regulation_id, f.entity_id))
    return flags
