"""Phase 4 confidence heuristics and override log."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_gov_map.confidence import (
    apply_judgment,
    evaluate_summary,
    run_reflag,
)
from ai_gov_map.confidence.heuristics import (
    detect_date_conflicts,
    detect_hedging,
    detect_low_confidence,
    detect_off_taxonomy,
)
from ai_gov_map.overrides import (
    OverrideRecord,
    add_override,
    effective_tier,
    list_overrides,
)
from ai_gov_map.overrides.store import load_overrides, write_overrides
from ai_gov_map.summarise.models import SummaryRecord
from ai_gov_map.summarise.store import append_summaries, load_summaries

_REPO = Path(__file__).resolve().parents[1]
_SEED_OVERRIDES = _REPO / "data" / "overrides.json"


def _summary(**kwargs) -> SummaryRecord:
    base = dict(
        id="doc:1",
        summary="Clear statement of Annex III high-risk duties.",
        risk_tier="high",
        rationale="Matches employment biometric obligations.",
        model="test",
        created_at="2026-07-18T00:00:00Z",
        confidence=0.8,
        needs_review=False,
    )
    base.update(kwargs)
    return SummaryRecord(**base)


def test_hedging_detection_flags_review():
    reasons = detect_hedging("The system may be high-risk and might require review.")
    assert reasons
    assert "hedging" in reasons[0].lower()

    judgment = evaluate_summary(
        _summary(
            summary="It appears the obligation is unclear and possibly limited.",
            confidence=0.9,
        )
    )
    assert judgment["needs_human_review"] is True
    assert any("hedging" in r for r in judgment["reasons"])


def test_date_conflict_detection():
    text = "Published in 2020, then revised in 2024 with conflicting dates."
    reasons = detect_date_conflicts(text, metadata_date="2024-06-13")
    assert reasons
    assert any("conflict" in r.lower() or "year" in r.lower() for r in reasons)

    # Metadata year far from prose years
    far = detect_date_conflicts(
        "Guidance issued in 2018 for operators.",
        metadata_date="2024-01-01",
    )
    assert any("metadata year" in r for r in far)

    clean = detect_date_conflicts(
        "Regulation dated 2024 sets duties.",
        metadata_date="2024-06-13",
    )
    assert clean == []


def test_off_taxonomy_and_empty_tier():
    assert detect_off_taxonomy("critical")
    assert detect_off_taxonomy("")
    assert detect_off_taxonomy("high") == []

    judgment = evaluate_summary(
        _summary(risk_tier="banana", confidence=0.9, summary="Solid prose.")
    )
    assert judgment["needs_human_review"] is True
    assert any("outside taxonomy" in r for r in judgment["reasons"])


def test_low_confidence_flags_review():
    assert detect_low_confidence(0.3)
    assert detect_low_confidence(0.9) == []
    judgment = evaluate_summary(_summary(confidence=0.4, summary="Definite high-risk rule."))
    assert judgment["needs_human_review"] is True
    assert any("low backend confidence" in r for r in judgment["reasons"])


def test_override_apply_precedence(tmp_path: Path):
    overrides = tmp_path / "overrides.json"
    summaries = tmp_path / "summaries.jsonl"
    append_summaries(
        summaries,
        [
            _summary(id="a", risk_tier="high"),
            _summary(id="b", risk_tier="minimal"),
        ],
    )
    add_override(
        doc_id="a",
        previous_tier="high",
        new_tier="limited",
        reason="Model over-scored a transparency chatbot as Annex III high.",
        overrides_path=overrides,
        overridden_by="tester",
    )

    assert effective_tier("a", overrides_path=overrides, summaries_path=summaries) == "limited"
    assert effective_tier("b", overrides_path=overrides, summaries_path=summaries) == "minimal"
    # Explicit summary_tier ignored when override present
    assert (
        effective_tier(
            "a",
            overrides_path=overrides,
            summary_tier="unacceptable",
        )
        == "limited"
    )
    # Without override file, fall back to provided tier
    assert effective_tier("z", overrides_path=overrides, summary_tier="minimal") == "minimal"


def test_seed_overrides_file_loads():
    assert _SEED_OVERRIDES.exists(), "data/overrides.json must be seeded for Phase 4"
    rows = load_overrides(_SEED_OVERRIDES)
    assert 5 <= len(rows) <= 10
    ids = {r.id for r in rows}
    assert len(ids) == len(rows)
    for r in rows:
        assert r.previous_tier in {"unacceptable", "high", "limited", "minimal"}
        assert r.new_tier in {"unacceptable", "high", "limited", "minimal"}
        assert r.previous_tier != r.new_tier
        assert len(r.reason.strip()) > 20
        assert r.overridden_at


def test_reflag_updates_needs_review_without_rewriting_text(tmp_path: Path):
    path = tmp_path / "summaries.jsonl"
    original = _summary(
        id="hedge:1",
        summary="The duty might apply; date unclear for 2019 vs 2024.",
        risk_tier="high",
        confidence=0.9,
        needs_review=False,
    )
    append_summaries(path, [original])
    stats = run_reflag(path, regulations_path=tmp_path / "missing.csv", dry_run=False)
    assert stats["total"] == 1
    assert stats["flagged"] == 1
    loaded = load_summaries(path)
    assert loaded[0].needs_review is True
    assert loaded[0].summary == original.summary


def test_apply_judgment_preserves_backend_flag():
    draft = _summary(
        summary="Plain definitive summary with no hedges.",
        confidence=0.9,
        needs_review=True,
    )
    judged, judgment = apply_judgment(draft, preserve_backend_flag=True)
    assert judged.needs_review is True
    assert judgment["needs_human_review"] is True
