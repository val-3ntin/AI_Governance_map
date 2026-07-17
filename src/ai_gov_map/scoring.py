"""Actor × pillar capacity scoring with institutional-decay weights."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

# Repo root: src/ai_gov_map/scoring.py → parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SCORES_PATH = _REPO_ROOT / "data" / "scores.csv"
_DEFAULT_ACTORS_PATH = _REPO_ROOT / "data" / "actors.csv"

ACTIVITY_WEIGHTS: dict[str, float] = {
    "ongoing_enforcement": 1.0,
    "active_soft": 0.7,
    "one_off_position": 0.4,
    "expired_dormant": 0.1,
}

PILLARS = [
    "Risk_Auditing",
    "Data_Privacy",
    "SME_Sandboxes",
    "Transparency",
    "Funding_Grants",
]

PILLAR_LABELS = {
    "Risk_Auditing": "Risk Auditing",
    "Data_Privacy": "Data Privacy",
    "SME_Sandboxes": "SME Sandboxes",
    "Transparency": "Transparency",
    "Funding_Grants": "Funding & Grants",
}

GROUP_COLORS = {
    "Government": "#0072CE",
    "Regional": "#2ECC71",
    "Industry": "#F5A623",
    "Civil Society": "#E63946",
    "Academia": "#9B59B6",
}


def _score_cell(
    mandate: int | float,
    activity_type: str,
    reach: int | float,
    last_year: int,
    year: int,
    decay: float,
    weights: dict[str, float] | None = None,
) -> float:
    """Score one actor–pillar cell; capped at 3.0."""
    w = weights or ACTIVITY_WEIGHTS
    activity_w = w[activity_type]
    reach_bonus = 1 + reach
    raw = mandate + activity_w * reach_bonus
    years_stale = max(0, year - int(last_year))
    return min(3.0, round(raw * (decay**years_stale), 2))


def load_data(
    scores_path: Path | str | None = None,
    actors_path: Path | str | None = None,
) -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, float], dict[str, dict[str, Any]]]:
    """Load actor×pillar matrix and actor metadata from flat CSV files.

    Returns
    -------
    structured_data
        Nested dict: actor → pillar → {mandate, activity_type, last_year, reach}
    weights
        Activity-type decay weights (same semantics as the original app).
    actor_meta
        actor → {group, city, lat, lon, color}
    """
    scores_file = Path(scores_path) if scores_path else _DEFAULT_SCORES_PATH
    actors_file = Path(actors_path) if actors_path else _DEFAULT_ACTORS_PATH

    scores_df = pd.read_csv(scores_file)
    actors_df = pd.read_csv(actors_file)

    structured: dict[str, dict[str, dict[str, Any]]] = {}
    for _, row in scores_df.iterrows():
        actor = row["actor"]
        pillar = row["pillar"]
        structured.setdefault(actor, {})[pillar] = {
            "mandate": int(row["mandate"]),
            "activity_type": str(row["activity_type"]),
            "last_year": int(row["last_year"]),
            "reach": int(row["reach"]),
        }

    actor_meta: dict[str, dict[str, Any]] = {}
    for _, row in actors_df.iterrows():
        actor_meta[row["actor"]] = {
            "group": row["group"],
            "city": row["city"],
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "color": row["color"],
        }

    return structured, dict(ACTIVITY_WEIGHTS), actor_meta


def compute_scores(
    structured_data: dict[str, dict[str, dict[str, Any]]],
    pillar: str,
    year: int,
    decay: float,
    weights: dict[str, float] | None = None,
) -> dict[str, float]:
    """Compute per-actor scores for one pillar at a simulation year."""
    w = weights or ACTIVITY_WEIGHTS
    scores: dict[str, float] = {}
    for actor, pillars in structured_data.items():
        cell = pillars[pillar]
        scores[actor] = _score_cell(
            mandate=cell["mandate"],
            activity_type=cell["activity_type"],
            reach=cell["reach"],
            last_year=cell["last_year"],
            year=year,
            decay=decay,
            weights=w,
        )
    return scores


def compute_heatmap(
    structured_data: dict[str, dict[str, dict[str, Any]]],
    year: int,
    decay: float,
    pillars: list[str] | None = None,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Full actor × pillar score matrix for the given simulation parameters."""
    pillar_list = pillars or PILLARS
    w = weights or ACTIVITY_WEIGHTS
    rows = []
    actors = list(structured_data.keys())
    for actor in actors:
        row = {}
        for p in pillar_list:
            cell = structured_data[actor][p]
            row[p] = _score_cell(
                mandate=cell["mandate"],
                activity_type=cell["activity_type"],
                reach=cell["reach"],
                last_year=cell["last_year"],
                year=year,
                decay=decay,
                weights=w,
            )
        rows.append(row)
    return pd.DataFrame(rows, index=actors)
