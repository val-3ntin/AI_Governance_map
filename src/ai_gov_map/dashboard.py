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
    "overridden",
    "confidence",
    "matched_entities",
    "matched_entity_names",
)

# Columns the Regulatory Feed table selects — keep in sync with app.py display.
FEED_DISPLAY_COLUMNS: tuple[str, ...] = (
    "date",
    "title",
    "source",
    "effective_tier",
    "needs_review",
    "overridden",
    "matched_entity_names",
    "jurisdiction",
    "url",
)

_BADGE_DEFAULTS: dict[str, Any] = {
    "effective_tier": "",
    "needs_review": False,
    "overridden": False,
}

ACCENT = "#0072CE"

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


def last_fetched_at(path: Path | str | None = None) -> str | None:
    """Return the max ``fetched_at`` ISO stamp from the regulation CSV, or None."""
    df = load_regulation_frame(path)
    if df.empty or "fetched_at" not in df.columns:
        return None
    stamps = [str(s).strip() for s in df["fetched_at"].tolist() if str(s).strip()]
    if not stamps:
        return None
    return max(stamps)


def format_refresh_label(fetched_at: str | None) -> str:
    """Human-readable refresh label for chrome (date-only when parseable)."""
    if not fetched_at:
        return "unknown"
    raw = str(fetched_at).strip()
    # Prefer YYYY-MM-DD prefix for quiet chrome.
    if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
        return raw[:10]
    parsed = pd.to_datetime(raw, errors="coerce", utc=True)
    if pd.isna(parsed):
        return raw
    return parsed.strftime("%Y-%m-%d")


def load_overrides_table(path: Path | str | None = None) -> pd.DataFrame:
    """Compact override log for the Feed judgement strip (id, was→now, reason)."""
    from ai_gov_map.overrides.store import load_overrides

    ov_path = Path(path) if path else DEFAULT_OVERRIDES
    cols = ["id", "previous_tier", "new_tier", "was_now", "reason", "overridden_at"]
    if not ov_path.is_file():
        return pd.DataFrame(columns=cols)
    rows: list[dict[str, Any]] = []
    for rec in load_overrides(ov_path):
        prev = (rec.previous_tier or "").strip().lower()
        nxt = (rec.new_tier or "").strip().lower()
        rows.append(
            {
                "id": rec.id,
                "previous_tier": prev,
                "new_tier": nxt,
                "was_now": f"{prev} → {nxt}",
                "reason": rec.reason or "",
                "overridden_at": rec.overridden_at or "",
            }
        )
    return pd.DataFrame(rows, columns=cols)


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


def ensure_monitor_columns(df: pd.DataFrame | None) -> pd.DataFrame:
    """Guarantee ``MONITOR_COLUMNS`` (incl. badge cols) exist with safe defaults.

    Defends against stale caches / partial frames so the Feed UI never KeyErrors
    on ``effective_tier``, ``needs_review``, or ``overridden``.
    """
    if df is None:
        return pd.DataFrame(columns=list(MONITOR_COLUMNS))
    out = df.copy()
    for col in MONITOR_COLUMNS:
        if col in out.columns:
            continue
        if col in _BADGE_DEFAULTS:
            out[col] = _BADGE_DEFAULTS[col]
        elif col == "confidence":
            out[col] = None
        else:
            out[col] = ""
    # Stable column order for export / UI.
    extras = [c for c in out.columns if c not in MONITOR_COLUMNS]
    return out[list(MONITOR_COLUMNS) + extras]


def feed_display_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Select Feed table columns that exist (intersection, order preserved)."""
    if df is None or df.empty:
        present = [c for c in FEED_DISPLAY_COLUMNS if df is not None and c in df.columns]
        return pd.DataFrame(columns=present or list(FEED_DISPLAY_COLUMNS))
    present = [c for c in FEED_DISPLAY_COLUMNS if c in df.columns]
    return df[present]


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
    is missing (graceful empty state for the Streamlit page). Always includes
    badge columns ``effective_tier``, ``needs_review``, and ``overridden``.
    """
    regs = load_regulation_frame(regulation_path)
    if regs.empty:
        return ensure_monitor_columns(pd.DataFrame(columns=list(MONITOR_COLUMNS)))

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
                "overridden": doc_id in overrides_index,
                "confidence": meta.get("confidence"),
                "matched_entities": ";".join(entity_ids),
                "matched_entity_names": "; ".join(names),
            }
        )

    df = ensure_monitor_columns(pd.DataFrame(rows, columns=list(MONITOR_COLUMNS)))
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
        return ensure_monitor_columns(
            pd.DataFrame(columns=list(MONITOR_COLUMNS) if df is None else df.columns)
        )

    out = ensure_monitor_columns(df)

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
        ov = rec.get("overridden")
        if isinstance(ov, (bool, int)):
            rec["overridden"] = bool(ov)
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
        colorway=[ACCENT],
    )
    return fig


def build_heatmap_figure(
    df_heat: pd.DataFrame,
    pillar_labels: dict[str, str] | None = None,
    *,
    flag_cells: list[tuple[str, int]] | None = None,
) -> go.Figure:
    """Plotly heatmap for the Capacity Matrix (lazy plotly import)."""
    import plotly.graph_objects as go

    labels = pillar_labels or {}
    if df_heat is None or df_heat.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No capacity data",
            height=360,
            template="plotly_white",
        )
        return fig

    x_labels = [labels.get(c, c) for c in df_heat.columns]
    y_labels = list(df_heat.index)
    z = df_heat.values.tolist()
    text = [[f"{v:.1f}" for v in row] for row in df_heat.values]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=x_labels,
            y=y_labels,
            text=text,
            texttemplate="%{text}",
            textfont={"size": 11, "color": "#0D1B2A"},
            colorscale=[
                [0.0, "#F7F8FA"],
                [0.33, "#B9D1EA"],
                [0.66, "#4A88C0"],
                [1.0, "#0C2C52"],
            ],
            zmin=0,
            zmax=3,
            colorbar=dict(
                tickvals=[0, 1, 2, 3],
                ticktext=["0 — Gap", "1 — Weak", "2 — Moderate", "3 — Strong"],
                thickness=14,
            ),
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}<extra></extra>",
            xgap=3,
            ygap=3,
        )
    )

    if flag_cells:
        flag_x: list[str] = []
        flag_y: list[str] = []
        for actor, pillar_idx in flag_cells:
            if actor not in df_heat.index:
                continue
            if pillar_idx < 0 or pillar_idx >= len(df_heat.columns):
                continue
            flag_x.append(x_labels[pillar_idx])
            flag_y.append(actor)
        if flag_x:
            fig.add_trace(
                go.Scatter(
                    x=flag_x,
                    y=flag_y,
                    mode="markers",
                    marker=dict(
                        size=9,
                        color="#E63946",
                        line=dict(width=1.2, color="white"),
                    ),
                    name="Intervention priority",
                    hoverinfo="skip",
                    showlegend=True,
                )
            )

    fig.update_layout(
        title="Dynamic capacity matrix",
        height=max(420, 28 * len(y_labels) + 120),
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig


def build_decay_bar_figure(
    series: pd.Series,
    *,
    title: str,
    subtitle: str = "",
) -> go.Figure:
    """Plotly horizontal bar chart for Decay Simulation (lazy plotly import)."""
    import plotly.graph_objects as go

    if series is None or series.empty:
        fig = go.Figure()
        fig.update_layout(title="No actors to display", height=360, template="plotly_white")
        return fig

    values = series.astype(float)
    colors = []
    for i, val in enumerate(values.values):
        if i == 0:
            colors.append("#E63946")
        elif val < 1.0:
            colors.append("#F5A623")
        else:
            colors.append(ACCENT)

    fig = go.Figure(
        data=go.Bar(
            x=values.values,
            y=list(values.index),
            orientation="h",
            marker_color=colors,
            text=[f"{v:.2f}" for v in values.values],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Score: %{x:.2f}<extra></extra>",
        )
    )
    fig.add_vline(x=1.0, line_dash="dash", line_color="#94A3B8", annotation_text="Weak (1.0)")
    fig.add_vline(x=2.0, line_dash="dot", line_color="#64748B", annotation_text="Moderate (2.0)")
    full_title = title if not subtitle else f"{title}<br><sup>{subtitle}</sup>"
    fig.update_layout(
        title=full_title,
        xaxis=dict(range=[0, 3.5], title="Simulated score", showgrid=False),
        yaxis=dict(autorange="reversed", title=""),
        height=max(360, 36 * len(values) + 100),
        template="plotly_white",
        margin=dict(l=20, r=40, t=70, b=40),
        showlegend=False,
    )
    return fig


__all__ = [
    "ACCENT",
    "FEED_DISPLAY_COLUMNS",
    "MONITOR_COLUMNS",
    "RISK_TIERS",
    "TIER_COLORS",
    "build_decay_bar_figure",
    "build_heatmap_figure",
    "build_monitor_frame",
    "build_timeline_figure",
    "dataframe_to_csv",
    "dataframe_to_json",
    "ensure_monitor_columns",
    "feed_display_frame",
    "filter_actors_by_group",
    "filter_monitor",
    "format_refresh_label",
    "last_fetched_at",
    "list_tracked_entities",
    "load_overrides_table",
    "load_regulation_frame",
]
