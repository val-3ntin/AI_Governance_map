"""Shared dashboard helpers for the Streamlit regulatory monitor (Phase 5).

Loaders, filters, export, and Plotly timeline builders live here so ``app.py``
stays thin. These functions are pure (no Streamlit) and unit-testable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from ai_gov_map.match.load import load_entities
from ai_gov_map.match.store import read_impact_flags
from ai_gov_map.overrides import effective_tier
from ai_gov_map.overrides.store import overrides_by_id
from ai_gov_map.summarise.models import RISK_TIERS
from ai_gov_map.summarise.store import load_summaries

if TYPE_CHECKING:
    import plotly.graph_objects as go

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGULATION = _REPO_ROOT / "data" / "regulation_data.csv"
DEFAULT_SUMMARIES = _REPO_ROOT / "data" / "summaries.jsonl"
DEFAULT_OVERRIDES = _REPO_ROOT / "data" / "overrides.json"
DEFAULT_ENTITIES = _REPO_ROOT / "data" / "entities.yaml"
DEFAULT_IMPACT_FLAGS = _REPO_ROOT / "data" / "impact_flags.csv"

MONITOR_COLUMNS: tuple[str, ...] = (
    "id",
    "date",
    "title",
    "source",
    "url",
    "jurisdiction",
    "text_excerpt",
    "summary_tier",
    "effective_tier",
    "needs_review",
    "confidence",
    "matched_entities",
    "matched_entity_names",
)

TIER_COLORS: dict[str, str] = {
    "unacceptable": "#8B0000",
    "high": "#C0392B",
    "limited": "#D4A017",
    "minimal": "#2E7D4F",
    "": "#7A8EA6",
}


def filter_actors_by_group(
    actors: list[str],
    actor_meta: dict[str, dict[str, Any]],
    groups: list[str],
) -> list[str]:
    """Return actors whose group is in ``groups`` (Phase 0 scoring UI)."""
    return [a for a in actors if actor_meta[a]["group"] in groups]


def load_regulation_frame(path: Path | str | None = None) -> pd.DataFrame:
    """Load ``regulation_data.csv``; empty frame if missing."""
    p = Path(path) if path else DEFAULT_REGULATION
    if not p.is_file():
        return pd.DataFrame(
            columns=[
                "id",
                "date",
                "title",
                "source",
                "url",
                "jurisdiction",
                "text_excerpt",
                "fetched_at",
            ]
        )
    df = pd.read_csv(p, dtype=str).fillna("")
    if "id" not in df.columns and "regulation_id" in df.columns:
        df = df.rename(columns={"regulation_id": "id"})
    return df


def _summaries_index(path: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Map doc id → last summary fields (tier, needs_review, confidence)."""
    p = Path(path) if path else DEFAULT_SUMMARIES
    if not p.is_file():
        return {}
    index: dict[str, dict[str, Any]] = {}
    for rec in load_summaries(p):
        index[rec.id] = {
            "summary_tier": (rec.risk_tier or "").strip().lower(),
            "needs_review": bool(rec.needs_review),
            "confidence": float(rec.confidence) if rec.confidence is not None else None,
            "summary": rec.summary or "",
        }
    return index


def list_tracked_entities(
    entities_path: Path | str | None = None,
    impact_flags_path: Path | str | None = None,
) -> list[dict[str, str]]:
    """Return ``[{id, display_name}, ...]`` from entities.yaml (+ flagged ids).

    Gracefully returns [] / partial lists when files are missing.
    """
    ent_path = Path(entities_path) if entities_path else DEFAULT_ENTITIES
    flags_path = Path(impact_flags_path) if impact_flags_path else DEFAULT_IMPACT_FLAGS

    by_id: dict[str, str] = {}
    if ent_path.is_file():
        try:
            for ent in load_entities(ent_path):
                by_id[ent.id] = ent.display_name or ent.id
        except (OSError, ValueError):
            pass

    if flags_path.is_file():
        for flag in read_impact_flags(flags_path):
            eid = (flag.entity_id or "").strip()
            if eid and eid not in by_id:
                by_id[eid] = eid

    return [{"id": eid, "display_name": name} for eid, name in sorted(by_id.items())]


def _entity_matches_by_regulation(
    impact_flags_path: Path | str | None = None,
) -> dict[str, list[str]]:
    """Map regulation_id → list of matched entity ids."""
    flags_path = Path(impact_flags_path) if impact_flags_path else DEFAULT_IMPACT_FLAGS
    mapping: dict[str, list[str]] = {}
    if not flags_path.is_file():
        return mapping
    for flag in read_impact_flags(flags_path):
        rid = (flag.regulation_id or "").strip()
        eid = (flag.entity_id or "").strip()
        if not rid or not eid:
            continue
        mapping.setdefault(rid, [])
        if eid not in mapping[rid]:
            mapping[rid].append(eid)
    return mapping


def build_monitor_frame(
    *,
    regulation_path: Path | str | None = None,
    summaries_path: Path | str | None = None,
    overrides_path: Path | str | None = None,
    entities_path: Path | str | None = None,
    impact_flags_path: Path | str | None = None,
) -> pd.DataFrame:
    """Join regulation feed with summaries, overrides, and entity impact flags.

    Returns an empty DataFrame with ``MONITOR_COLUMNS`` when the regulation CSV
    is missing (graceful empty state for the Streamlit page).
    """
    regs = load_regulation_frame(regulation_path)
    if regs.empty:
        return pd.DataFrame(columns=list(MONITOR_COLUMNS))

    summaries = _summaries_index(summaries_path)
    ov_path = Path(overrides_path) if overrides_path else DEFAULT_OVERRIDES
    overrides_index = overrides_by_id(ov_path) if ov_path.is_file() else {}

    entity_lookup = {
        e["id"]: e["display_name"]
        for e in list_tracked_entities(entities_path, impact_flags_path)
    }
    matches = _entity_matches_by_regulation(impact_flags_path)

    rows: list[dict[str, Any]] = []
    for _, row in regs.iterrows():
        doc_id = str(row.get("id") or "").strip()
        if not doc_id:
            continue
        meta = summaries.get(doc_id, {})
        summary_tier = meta.get("summary_tier") or ""
        tier = effective_tier(
            doc_id,
            summary_tier=summary_tier or None,
            overrides_index=overrides_index,
        )
        entity_ids = matches.get(doc_id, [])
        names = [entity_lookup.get(e, e) for e in entity_ids]
        rows.append(
            {
                "id": doc_id,
                "date": str(row.get("date") or "").strip(),
                "title": str(row.get("title") or "").strip(),
                "source": str(row.get("source") or "").strip(),
                "url": str(row.get("url") or "").strip(),
                "jurisdiction": str(row.get("jurisdiction") or "").strip(),
                "text_excerpt": str(row.get("text_excerpt") or "").strip(),
                "summary_tier": summary_tier,
                "effective_tier": (tier or "").strip().lower(),
                "needs_review": bool(meta.get("needs_review", False)),
                "confidence": meta.get("confidence"),
                "matched_entities": ";".join(entity_ids),
                "matched_entity_names": "; ".join(names),
            }
        )

    df = pd.DataFrame(rows, columns=list(MONITOR_COLUMNS))
    if not df.empty and "date" in df.columns:
        df = df.sort_values(by=["date", "id"], ascending=[False, True], kind="mergesort")
        df = df.reset_index(drop=True)
    return df


def filter_monitor(
    df: pd.DataFrame,
    *,
    entity_ids: list[str] | None = None,
    risk_tiers: list[str] | None = None,
    query: str | None = None,
) -> pd.DataFrame:
    """Filter the monitor frame by entities, effective risk tiers, and text.

    - ``entity_ids``: keep rows that match *any* selected entity (via
      ``matched_entities``). Empty / None = no entity filter.
    - ``risk_tiers``: keep rows whose ``effective_tier`` is in the set.
      Empty / None = no tier filter.
    - ``query``: case-insensitive substring on ``title`` + ``text_excerpt``.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=list(MONITOR_COLUMNS) if df is None else df.columns)

    out = df.copy()

    if entity_ids:
        wanted = {e.strip() for e in entity_ids if e and str(e).strip()}
        if wanted:

            def _matches_entity(cell: Any) -> bool:
                ids = {x.strip() for x in str(cell or "").split(";") if x.strip()}
                return bool(ids & wanted)

            out = out[out["matched_entities"].map(_matches_entity)]

    if risk_tiers:
        tiers = {t.strip().lower() for t in risk_tiers if t and str(t).strip()}
        if tiers:
            out = out[out["effective_tier"].str.lower().isin(tiers)]

    if query and str(query).strip():
        q = str(query).strip().lower()
        title = out["title"].fillna("").str.lower()
        excerpt = out["text_excerpt"].fillna("").str.lower()
        out = out[title.str.contains(q, regex=False) | excerpt.str.contains(q, regex=False)]

    return out.reset_index(drop=True)


def dataframe_to_csv(df: pd.DataFrame) -> str:
    """Serialize filtered monitor rows to CSV text (UTF-8)."""
    if df is None or df.empty:
        return pd.DataFrame(columns=list(MONITOR_COLUMNS)).to_csv(index=False)
    return df.to_csv(index=False)


def dataframe_to_json(df: pd.DataFrame) -> str:
    """Serialize filtered monitor rows to a JSON array string."""
    if df is None or df.empty:
        return "[]"
    records = df.to_dict(orient="records")
    # JSON-friendly: bools/None stay; cast NaN confidence
    for rec in records:
        conf = rec.get("confidence")
        if conf is not None and isinstance(conf, float) and pd.isna(conf):
            rec["confidence"] = None
        nr = rec.get("needs_review")
        if isinstance(nr, (bool, int)):
            rec["needs_review"] = bool(nr)
    return json.dumps(records, ensure_ascii=False, indent=2)


def build_timeline_figure(df: pd.DataFrame) -> go.Figure:
    """Plotly scatter timeline of regulatory items by date and risk tier."""
    import plotly.express as px
    import plotly.graph_objects as go

    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No regulatory items to display",
            xaxis_title="Date",
            yaxis_title="Source",
            height=360,
            template="plotly_white",
        )
        return fig

    plot_df = df.copy()
    plot_df["date_parsed"] = pd.to_datetime(plot_df["date"], errors="coerce")
    plot_df = plot_df.dropna(subset=["date_parsed"])
    if plot_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No parseable dates in filtered view",
            height=360,
            template="plotly_white",
        )
        return fig

    plot_df["tier_label"] = plot_df["effective_tier"].replace("", "(unscored)")
    plot_df["review_marker"] = plot_df["needs_review"].map(
        lambda x: "needs review" if x else "ok"
    )
    hover = (
        "<b>%{customdata[0]}</b><br>"
        "Source: %{customdata[1]}<br>"
        "Tier: %{customdata[2]}<br>"
        "Review: %{customdata[3]}<br>"
        "Entities: %{customdata[4]}<extra></extra>"
    )
    fig = px.scatter(
        plot_df,
        x="date_parsed",
        y="source",
        color="tier_label",
        color_discrete_map={
            **{k: v for k, v in TIER_COLORS.items() if k},
            "(unscored)": "#7A8EA6",
        },
        symbol="review_marker",
        custom_data=[
            "title",
            "source",
            "effective_tier",
            "review_marker",
            "matched_entity_names",
        ],
        category_orders={
            "tier_label": [
                t for t in RISK_TIERS if t in set(plot_df["tier_label"])
            ]
            + (["(unscored)"] if "(unscored)" in set(plot_df["tier_label"]) else []),
        },
    )
    fig.update_traces(marker=dict(size=11, line=dict(width=0.5, color="#0D1B2A")), hovertemplate=hover)
    fig.update_layout(
        title="Regulatory feed timeline",
        xaxis_title="Date",
        yaxis_title="Source",
        legend_title="Effective risk tier",
        height=420,
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


__all__ = [
    "MONITOR_COLUMNS",
    "RISK_TIERS",
    "TIER_COLORS",
    "build_monitor_frame",
    "build_timeline_figure",
    "dataframe_to_csv",
    "dataframe_to_json",
    "filter_actors_by_group",
    "filter_monitor",
    "list_tracked_entities",
    "load_regulation_frame",
]
