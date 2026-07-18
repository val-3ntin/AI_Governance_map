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


def _toy_actor(
    mandate: int = 1,
    activity_type: str = "ongoing_enforcement",
    reach: int = 1,
    last_year: int = 2024,
) -> dict:
    return {
        "Toy": {
            "Risk_Auditing": {
                "mandate": mandate,
                "activity_type": activity_type,
                "last_year": last_year,
                "reach": reach,
            }
        }
    }


def test_score_no_decay_when_year_equals_last_year():
    data = _toy_actor(mandate=1, activity_type="ongoing_enforcement", reach=1, last_year=2025)
    # raw = 1 + 1.0 * (1+1) = 3.0
    scores = compute_scores(data, "Risk_Auditing", year=2025, decay=0.88)
    assert scores["Toy"] == 3.0


def test_score_no_decay_when_year_before_last_year():
    """Future-dated last_year must not inflate via negative exponents."""
    data = _toy_actor(mandate=1, activity_type="active_soft", reach=0, last_year=2030)
    # raw = 1 + 0.7 * 1 = 1.7
    scores = compute_scores(data, "Risk_Auditing", year=2025, decay=0.5)
    assert scores["Toy"] == 1.7


def test_score_caps_at_three():
    data = _toy_actor(mandate=2, activity_type="ongoing_enforcement", reach=2, last_year=2025)
    # raw = 2 + 1.0 * 3 = 5.0 → capped
    scores = compute_scores(data, "Risk_Auditing", year=2025, decay=0.88)
    assert scores["Toy"] == 3.0


def test_dormant_weight_decays_faster_than_enforcement():
    dormant = _toy_actor(mandate=1, activity_type="expired_dormant", reach=1, last_year=2020)
    active = _toy_actor(mandate=1, activity_type="ongoing_enforcement", reach=1, last_year=2020)
    d = compute_scores(dormant, "Risk_Auditing", year=2025, decay=0.88)["Toy"]
    a = compute_scores(active, "Risk_Auditing", year=2025, decay=0.88)["Toy"]
    assert d < a
    assert d > 0


def test_decay_factor_one_preserves_raw_score():
    data = _toy_actor(mandate=1, activity_type="one_off_position", reach=1, last_year=2015)
    # raw = 1 + 0.4 * 2 = 1.8; decay**years = 1
    scores = compute_scores(data, "Risk_Auditing", year=2030, decay=1.0)
    assert scores["Toy"] == 1.8
