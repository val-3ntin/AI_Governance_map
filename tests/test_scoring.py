"""Smoke tests for capacity scoring (preserve original app semantics)."""

from __future__ import annotations

from ai_gov_map.scoring import (
    ACTIVITY_WEIGHTS,
    PILLARS,
    compute_heatmap,
    compute_scores,
    load_data,
)


def test_load_data_has_twelve_actors_and_five_pillars():
    data, weights, meta = load_data()
    assert len(data) == 12
    assert set(weights) == set(ACTIVITY_WEIGHTS)
    assert len(meta) == 12
    for actor, pillars in data.items():
        assert set(pillars) == set(PILLARS)
        assert actor in meta


def test_garante_risk_auditing_fresh_score():
    """Ongoing enforcement + mandate + reach, year == last_year → no decay."""
    data, _, _ = load_data()
    scores = compute_scores(data, "Risk_Auditing", year=2025, decay=0.88)
    # mandate 1 + 1.0 * (1 + 1) = 3.0, capped at 3.0
    assert scores["Garante (DPA)"] == 3.0


def test_decay_reduces_dormant_scores():
    data, _, _ = load_data()
    fresh = compute_scores(data, "Risk_Auditing", year=2021, decay=0.88)
    stale = compute_scores(data, "Risk_Auditing", year=2030, decay=0.88)
    # CDP Risk_Auditing is expired_dormant from 2021 — must fall by 2030
    assert stale["CDP"] < fresh["CDP"]


def test_heatmap_shape():
    data, _, _ = load_data()
    df = compute_heatmap(data, year=2026, decay=0.88)
    assert df.shape == (12, 5)
    assert list(df.columns) == PILLARS
    assert (df <= 3.0).all().all()
