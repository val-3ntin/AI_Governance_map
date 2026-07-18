"""Phase 3 match: keyword/taxonomy impact flags (no network)."""

from __future__ import annotations

from pathlib import Path

import yaml

from ai_gov_map.ingest.models import RegulationRecord
from ai_gov_map.ingest.normalize import write_csv
from ai_gov_map.match import run_match
from ai_gov_map.match.load import load_entities, load_risk_tiers
from ai_gov_map.match.matcher import match_all, match_pair, score_match
from ai_gov_map.match.models import Entity, ImpactFlag
from ai_gov_map.match.store import read_impact_flags, write_impact_flags


def _rec(**kwargs) -> RegulationRecord:
    base = dict(
        id="doc:1",
        date="2024-06-13",
        title="EU AI Act guidance",
        source="EUR-Lex",
        url="https://example.com/1",
        jurisdiction="EU",
        text_excerpt="High-risk obligations.",
        fetched_at="2024-07-01T00:00:00Z",
    )
    base.update(kwargs)
    return RegulationRecord(**base)


def _entity(**kwargs) -> Entity:
    base = dict(
        id="hyp-test-01",
        display_name="Test Org (hypothetical)",
        sector="healthcare",
        ai_use_cases=("clinical_decision_support",),
        keywords=("healthcare", "sanità"),
        risk_exposure="high",
        notes="fixture",
        hypothetical=True,
    )
    base.update(kwargs)
    return Entity(**base)


def _write_entities(path: Path, entities: list[dict]) -> None:
    path.write_text(
        yaml.safe_dump(
            {"meta": {"hypothetical": True}, "entities": entities},
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def test_no_match_when_no_overlap():
    entity = _entity(keywords=("biometrics",), ai_use_cases=("facial_recognition",), sector="biometrics")
    record = _rec(title="OECD soft strategy webinar", text_excerpt="Open consultations only.")
    score, terms, reason = score_match(entity, record)
    assert score == 0.0
    assert terms == []
    assert match_pair(entity, record) is None
    assert "no overlap" in reason or reason == "no overlap"


def test_keyword_hit_emits_flag():
    entity = _entity()
    record = _rec(
        title="Responsible AI for sanità digitale",
        text_excerpt="Healthcare providers adopt clinical tools.",
    )
    flag = match_pair(entity, record, risk_tier="high")
    assert flag is not None
    assert flag.entity_id == "hyp-test-01"
    assert flag.regulation_id == "doc:1"
    assert flag.match_score >= 1.0
    assert "healthcare" in flag.matched_terms or "sanità" in flag.matched_terms
    assert flag.risk_tier == "high"
    assert flag.flagged_at == "2024-07-01T00:00:00Z"


def test_case_insensitivity():
    entity = _entity(keywords=("High-Risk", "ANNEX III"), ai_use_cases=(), sector="compliance_advisory")
    record = _rec(
        title="Guidance on high-risk annex iii systems",
        text_excerpt="",
    )
    score, terms, _ = score_match(entity, record)
    assert score >= 1.0
    assert "high-risk" in terms
    assert "annex iii" in terms


def test_multi_entity_independent_flags():
    health = _entity(id="hyp-health", keywords=("sanità",), ai_use_cases=(), sector="healthcare")
    hr = _entity(
        id="hyp-hr",
        display_name="HR (hypothetical)",
        sector="hr_recruitment",
        ai_use_cases=("recruitment_screening",),
        keywords=("lavoro",),
        risk_exposure="high",
    )
    finance = _entity(
        id="hyp-fin",
        display_name="Fin (hypothetical)",
        sector="finance",
        ai_use_cases=(),
        keywords=("credit scoring",),
        risk_exposure="high",
    )
    regs = [
        _rec(id="r:health", title="IA in sanità", text_excerpt=""),
        _rec(id="r:hr", title="IA e lavoro avviso", text_excerpt=""),
        _rec(id="r:none", title="Domain candidature ICANN", text_excerpt=""),
    ]
    flags = match_all([health, hr, finance], regs)
    pairs = {(f.regulation_id, f.entity_id) for f in flags}
    assert ("r:health", "hyp-health") in pairs
    assert ("r:hr", "hyp-hr") in pairs
    assert ("r:none", "hyp-health") not in pairs
    assert ("r:none", "hyp-hr") not in pairs
    assert ("r:none", "hyp-fin") not in pairs
    # Stable sort
    assert flags == sorted(flags, key=lambda f: (f.regulation_id, f.entity_id))


def test_empty_inputs_yield_no_flags(tmp_path: Path):
    assert match_all([], []) == []
    assert match_all([_entity()], []) == []
    assert match_all([], [_rec()]) == []

    empty_ent = tmp_path / "entities.yaml"
    _write_entities(empty_ent, [])
    regs = tmp_path / "regs.csv"
    write_csv(regs, [])
    out = tmp_path / "impact_flags.csv"
    stats = run_match(empty_ent, regs, None, out, skip_summaries=True)
    assert stats["flags"] == 0
    assert stats["entities"] == 0
    assert out.is_file()
    assert read_impact_flags(out) == []


def test_run_match_writes_csv_and_is_deterministic(tmp_path: Path):
    ents = tmp_path / "entities.yaml"
    _write_entities(
        ents,
        [
            {
                "id": "hyp-a",
                "display_name": "A (hypothetical)",
                "sector": "education",
                "ai_use_cases": ["student_assessment"],
                "keywords": ["scuola", "education"],
                "risk_exposure": "high",
                "notes": "fixture",
            }
        ],
    )
    regs = tmp_path / "regs.csv"
    write_csv(
        regs,
        [
            _rec(
                id="doc:edu",
                title="IA a scuola — Garante chiede informazioni",
                text_excerpt="Education institutes using AI.",
                fetched_at="2026-07-01T12:00:00Z",
            )
        ],
    )
    summaries = tmp_path / "summaries.jsonl"
    summaries.write_text(
        '{"id":"doc:edu","risk_tier":"high","summary":"x","rationale":"y",'
        '"model":"offline","created_at":"2026-07-01T00:00:00Z"}\n',
        encoding="utf-8",
    )
    out = tmp_path / "impact_flags.csv"
    stats1 = run_match(ents, regs, summaries, out)
    stats2 = run_match(ents, regs, summaries, out)
    assert stats1["flags"] == stats2["flags"] == 1
    rows1 = read_impact_flags(out)
    rows2 = read_impact_flags(out)
    assert rows1 == rows2
    assert rows1[0].entity_id == "hyp-a"
    assert rows1[0].risk_tier == "high"
    assert "scuola" in rows1[0].matched_terms or "education" in rows1[0].matched_terms


def test_load_entities_and_risk_tiers(tmp_path: Path):
    path = tmp_path / "entities.yaml"
    _write_entities(
        path,
        [
            {
                "id": "hyp-x",
                "display_name": "X (hypothetical)",
                "sector": "finance",
                "ai_use_cases": ["credit_scoring"],
                "keywords": ["credit"],
            }
        ],
    )
    entities = load_entities(path)
    assert len(entities) == 1
    assert entities[0].id == "hyp-x"
    assert entities[0].hypothetical is True

    jl = tmp_path / "s.jsonl"
    jl.write_text(
        '{"id":"a","risk_tier":"minimal"}\n{"id":"b","risk_tier":"HIGH"}\n',
        encoding="utf-8",
    )
    tiers = load_risk_tiers(jl)
    assert tiers["a"] == "minimal"
    assert tiers["b"] == "high"
    assert load_risk_tiers(None) == {}


def test_write_impact_flags_schema(tmp_path: Path):
    out = tmp_path / "flags.csv"
    flag = ImpactFlag(
        regulation_id="r1",
        entity_id="e1",
        match_score=1.5,
        matched_terms="healthcare",
        risk_tier="high",
        reason="keywords=healthcare",
        flagged_at="2026-07-18T00:00:00Z",
    )
    write_impact_flags(out, [flag])
    text = out.read_text(encoding="utf-8")
    header = text.splitlines()[0]
    assert header == (
        "regulation_id,entity_id,match_score,matched_terms,risk_tier,reason,flagged_at"
    )
    loaded = read_impact_flags(out)
    assert loaded[0].match_score == 1.5
