"""Phase 5 dashboard loaders, filters, and export helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ai_gov_map.dashboard import (
    MONITOR_COLUMNS,
    build_monitor_frame,
    build_timeline_figure,
    dataframe_to_csv,
    dataframe_to_json,
    filter_monitor,
    list_tracked_entities,
    load_regulation_frame,
)

@pytest.fixture()
def fixture_dir(tmp_path: Path) -> Path:
    """Minimal regulation + summary + override + entity + flag set."""
    reg = tmp_path / "regulation_data.csv"
    reg.write_text(
        "id,date,title,source,url,jurisdiction,text_excerpt,fetched_at\n"
        "doc:a,2024-06-01,AI Act biometric ban,EUR-Lex,https://example.com/a,EU,"
        "Prohibits real-time biometric identification in public spaces,2024-06-01T00:00:00Z\n"
        "doc:b,2025-01-15,AgID digital academy update,AgID,https://example.com/b,IT,"
        "Training catalogue for public administration AI literacy,2025-01-15T00:00:00Z\n"
        "doc:c,2025-03-01,Healthcare AI guidance,Garante,https://example.com/c,IT,"
        "Guidance for sanità and clinical decision support systems,2025-03-01T00:00:00Z\n",
        encoding="utf-8",
    )

    summaries = tmp_path / "summaries.jsonl"
    summaries.write_text(
        json.dumps(
            {
                "id": "doc:a",
                "summary": "Biometric ban under AI Act.",
                "risk_tier": "unacceptable",
                "rationale": "Real-time biometric ID.",
                "model": "test",
                "created_at": "2025-01-01T00:00:00Z",
                "confidence": 0.9,
                "needs_review": False,
            }
        )
        + "\n"
        + json.dumps(
            {
                "id": "doc:b",
                "summary": "Academy update.",
                "risk_tier": "high",
                "rationale": "Keyword over-fire.",
                "model": "test",
                "created_at": "2025-01-01T00:00:00Z",
                "confidence": 0.4,
                "needs_review": True,
            }
        )
        + "\n"
        + json.dumps(
            {
                "id": "doc:c",
                "summary": "Health guidance.",
                "risk_tier": "minimal",
                "rationale": "Under-scored.",
                "model": "test",
                "created_at": "2025-01-01T00:00:00Z",
                "confidence": 0.5,
                "needs_review": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    overrides = tmp_path / "overrides.json"
    overrides.write_text(
        json.dumps(
            [
                {
                    "id": "doc:b",
                    "previous_tier": "high",
                    "new_tier": "minimal",
                    "reason": "Training content, not Annex III.",
                    "overridden_at": "2025-01-02T00:00:00Z",
                    "overridden_by": "analyst",
                },
                {
                    "id": "doc:c",
                    "previous_tier": "minimal",
                    "new_tier": "high",
                    "reason": "Clinical decision support is high-risk.",
                    "overridden_at": "2025-01-02T00:00:00Z",
                    "overridden_by": "analyst",
                },
            ],
            indent=2,
        ),
        encoding="utf-8",
    )

    entities = tmp_path / "entities.yaml"
    entities.write_text(
        "meta:\n  hypothetical: true\n"
        "entities:\n"
        "  - id: hyp-health-01\n"
        "    display_name: Northern Care Network\n"
        "    sector: healthcare\n"
        "    keywords: [healthcare, sanità]\n"
        "  - id: hyp-pa-05\n"
        "    display_name: Public Admin Hub\n"
        "    sector: public_admin\n"
        "    keywords: [agid, academy]\n",
        encoding="utf-8",
    )

    flags = tmp_path / "impact_flags.csv"
    flags.write_text(
        "regulation_id,entity_id,match_score,matched_terms,risk_tier,reason,flagged_at\n"
        "doc:b,hyp-pa-05,1.0,agid,minimal,keywords=agid,2025-01-01T00:00:00Z\n"
        "doc:c,hyp-health-01,1.2,sanità,high,keywords=sanità,2025-01-01T00:00:00Z\n",
        encoding="utf-8",
    )

    return tmp_path


def test_load_regulation_missing_returns_empty(tmp_path: Path):
    df = load_regulation_frame(tmp_path / "nope.csv")
    assert df.empty
    assert "id" in df.columns


def test_build_monitor_frame_applies_effective_tier(fixture_dir: Path):
    df = build_monitor_frame(
        regulation_path=fixture_dir / "regulation_data.csv",
        summaries_path=fixture_dir / "summaries.jsonl",
        overrides_path=fixture_dir / "overrides.json",
        entities_path=fixture_dir / "entities.yaml",
        impact_flags_path=fixture_dir / "impact_flags.csv",
    )
    assert list(df.columns) == list(MONITOR_COLUMNS)
    assert len(df) == 3
    by_id = df.set_index("id")
    assert by_id.loc["doc:a", "effective_tier"] == "unacceptable"
    assert by_id.loc["doc:b", "effective_tier"] == "minimal"  # overridden
    assert by_id.loc["doc:c", "effective_tier"] == "high"  # overridden
    assert by_id.loc["doc:b", "needs_review"] is True or bool(by_id.loc["doc:b", "needs_review"])
    assert "hyp-pa-05" in str(by_id.loc["doc:b", "matched_entities"])
    assert "Northern Care" in str(by_id.loc["doc:c", "matched_entity_names"])


def test_filter_monitor_by_entity_tier_and_query(fixture_dir: Path):
    df = build_monitor_frame(
        regulation_path=fixture_dir / "regulation_data.csv",
        summaries_path=fixture_dir / "summaries.jsonl",
        overrides_path=fixture_dir / "overrides.json",
        entities_path=fixture_dir / "entities.yaml",
        impact_flags_path=fixture_dir / "impact_flags.csv",
    )

    by_entity = filter_monitor(df, entity_ids=["hyp-health-01"])
    assert list(by_entity["id"]) == ["doc:c"]

    by_tier = filter_monitor(df, risk_tiers=["minimal"])
    assert set(by_tier["id"]) == {"doc:b"}

    by_query = filter_monitor(df, query="biometric")
    assert list(by_query["id"]) == ["doc:a"]

    combined = filter_monitor(
        df,
        entity_ids=["hyp-pa-05", "hyp-health-01"],
        risk_tiers=["high", "minimal"],
        query="guidance",
    )
    assert list(combined["id"]) == ["doc:c"]


def test_export_csv_and_json_match_filtered_rows(fixture_dir: Path):
    df = build_monitor_frame(
        regulation_path=fixture_dir / "regulation_data.csv",
        summaries_path=fixture_dir / "summaries.jsonl",
        overrides_path=fixture_dir / "overrides.json",
        entities_path=fixture_dir / "entities.yaml",
        impact_flags_path=fixture_dir / "impact_flags.csv",
    )
    filtered = filter_monitor(df, risk_tiers=["high"])
    csv_text = dataframe_to_csv(filtered)
    json_text = dataframe_to_json(filtered)

    assert "doc:c" in csv_text
    assert "doc:a" not in csv_text
    records = json.loads(json_text)
    assert isinstance(records, list)
    assert len(records) == 1
    assert records[0]["id"] == "doc:c"
    assert records[0]["effective_tier"] == "high"


def test_empty_monitor_and_timeline(tmp_path: Path):
    empty = build_monitor_frame(regulation_path=tmp_path / "missing.csv")
    assert empty.empty
    assert list(empty.columns) == list(MONITOR_COLUMNS)

    filtered = filter_monitor(empty, entity_ids=["x"], risk_tiers=["high"], query="zzz")
    assert filtered.empty
    assert dataframe_to_json(filtered) == "[]"
    assert "id" in dataframe_to_csv(filtered)

    fig = build_timeline_figure(empty)
    assert fig is not None
    assert "No regulatory" in (fig.layout.title.text or "")


def test_list_tracked_entities(fixture_dir: Path):
    ents = list_tracked_entities(
        fixture_dir / "entities.yaml",
        fixture_dir / "impact_flags.csv",
    )
    ids = {e["id"] for e in ents}
    assert "hyp-health-01" in ids
    assert "hyp-pa-05" in ids
    names = {e["id"]: e["display_name"] for e in ents}
    assert "Northern Care" in names["hyp-health-01"]
