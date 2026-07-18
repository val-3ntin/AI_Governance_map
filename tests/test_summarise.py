"""Phase 2 summarise: taxonomy validation, skip-known-IDs, JSONL, backends."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_gov_map.ingest.models import RegulationRecord
from ai_gov_map.ingest.normalize import write_csv
from ai_gov_map.summarise import run_summarise
from ai_gov_map.summarise.backends import (
    BackendError,
    HuggingFaceBackend,
    OfflineBackend,
    OllamaBackend,
    resolve_backend,
)
from ai_gov_map.summarise.models import RISK_TIERS
from ai_gov_map.summarise.prompt import (
    normalise_risk_tier,
    parse_model_response,
    truncate_words,
)
from ai_gov_map.summarise.store import append_summaries, known_ids, load_summaries
from ai_gov_map.summarise.models import SummaryRecord


def _rec(**kwargs) -> RegulationRecord:
    base = dict(
        id="doc:1",
        date="2024-06-13",
        title="EU AI Act guidance on high-risk systems",
        source="EUR-Lex",
        url="https://example.com/1",
        jurisdiction="EU",
        text_excerpt="Regulation (EU) 2024/1689 high-risk Annex III obligations.",
        fetched_at="2024-07-01T00:00:00Z",
    )
    base.update(kwargs)
    return RegulationRecord(**base)


def test_normalise_risk_tier_closed_taxonomy():
    assert set(RISK_TIERS) == {"unacceptable", "high", "limited", "minimal"}
    assert normalise_risk_tier("HIGH") == "high"
    assert normalise_risk_tier("high-risk") == "high"
    assert normalise_risk_tier("Limited Risk") == "limited"
    assert normalise_risk_tier("prohibited") == "unacceptable"
    assert normalise_risk_tier("low risk") == "minimal"
    assert normalise_risk_tier("banana") is None


def test_parse_model_response_invalid_tier_sets_needs_review():
    parsed = parse_model_response(
        '{"summary": "A short summary.", "risk_tier": "critical", "rationale": "x"}'
    )
    assert parsed["risk_tier"] in RISK_TIERS
    assert parsed["needs_review"] is True
    assert parsed["confidence"] < 0.5


def test_parse_model_response_valid_json():
    parsed = parse_model_response(
        'Here you go:\n```json\n{"summary": "Plain summary of the act.", '
        '"risk_tier": "high", "rationale": "Annex III style duties."}\n```'
    )
    assert parsed["risk_tier"] == "high"
    assert parsed["needs_review"] is False
    assert "Plain summary" in parsed["summary"]
    assert len(parsed["summary"].split()) <= 120


def test_truncate_words():
    text = " ".join(f"w{i}" for i in range(150))
    out = truncate_words(text, 120)
    assert len(out.split()) <= 121  # may include ellipsis token glued
    assert out.endswith("…")


def test_jsonl_append_and_known_ids(tmp_path: Path):
    path = tmp_path / "summaries.jsonl"
    a = SummaryRecord(
        id="a",
        summary="s",
        risk_tier="minimal",
        rationale="r",
        model="offline:rules-v1",
        created_at="2024-01-01T00:00:00Z",
        confidence=0.4,
        needs_review=True,
    )
    b = SummaryRecord(
        id="b",
        summary="s2",
        risk_tier="high",
        rationale="r2",
        model="offline:rules-v1",
        created_at="2024-01-02T00:00:00Z",
    )
    assert append_summaries(path, [a]) == 1
    assert known_ids(path) == {"a"}
    assert append_summaries(path, [b]) == 1
    loaded = load_summaries(path)
    assert [r.id for r in loaded] == ["a", "b"]
    assert loaded[1].risk_tier == "high"


def test_skip_known_ids_idempotent(tmp_path: Path):
    csv_path = tmp_path / "regs.csv"
    out = tmp_path / "summaries.jsonl"
    write_csv(
        csv_path,
        [
            _rec(id="keep:1", title="Webinar on open data culture"),
            _rec(id="new:2", title="AI workplace emotion monitoring plugin"),
        ],
    )
    # Seed first id
    append_summaries(
        out,
        [
            SummaryRecord(
                id="keep:1",
                summary="existing",
                risk_tier="minimal",
                rationale="seed",
                model="offline:rules-v1",
                created_at="2024-01-01T00:00:00Z",
            )
        ],
    )
    stats1 = run_summarise(csv_path, out, backend="offline")
    assert stats1["written"] == 1
    assert stats1["skipped"] == 1
    ids = [r.id for r in load_summaries(out)]
    assert ids == ["keep:1", "new:2"]

    stats2 = run_summarise(csv_path, out, backend="offline")
    assert stats2["written"] == 0
    assert stats2["skipped"] == 2
    assert len(load_summaries(out)) == 2


def test_offline_backend_produces_taxonomy_tier():
    backend = OfflineBackend()
    out = backend.summarise(_rec())
    assert out["risk_tier"] in RISK_TIERS
    assert out["model"].startswith("offline:")
    assert out["needs_review"] is True
    assert len(out["summary"].split()) <= 120


def test_ollama_backend_mocked_http():
    sess = MagicMock()
    tags = MagicMock()
    tags.status_code = 200
    tags.json.return_value = {"models": [{"name": "llama3.1:8b"}]}
    tags.raise_for_status = MagicMock()
    gen = MagicMock()
    gen.status_code = 200
    gen.json.return_value = {
        "response": json.dumps(
            {
                "summary": "The AI Act sets harmonised rules.",
                "risk_tier": "high",
                "rationale": "Primary EU AI Act text.",
            }
        )
    }
    gen.raise_for_status = MagicMock()
    sess.get.return_value = tags
    sess.post.return_value = gen

    backend = OllamaBackend(session=sess, model="llama3.1:8b")
    result = backend.summarise(_rec())
    assert result["risk_tier"] == "high"
    assert result["model"] == "ollama:llama3.1:8b"
    sess.post.assert_called_once()
    assert "/api/generate" in sess.post.call_args.args[0]


def test_hf_backend_mocked_http():
    sess = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = [
        {
            "generated_text": json.dumps(
                {
                    "summary": "Privacy authority sanctions a chatbot.",
                    "risk_tier": "high",
                    "rationale": "Child protection and biometric-adjacent concerns.",
                }
            )
        }
    ]
    resp.raise_for_status = MagicMock()
    sess.post.return_value = resp

    backend = HuggingFaceBackend(session=sess, token="hf_test_token")
    result = backend.summarise(
        _rec(
            title="Garante sanctions Character.AI over minors",
            source="Garante",
            text_excerpt="Age verification failures.",
        )
    )
    assert result["risk_tier"] == "high"
    assert result["model"].startswith("hf:")
    assert "Authorization" in sess.post.call_args.kwargs["headers"]


def test_resolve_backend_auto_falls_to_offline():
    with patch("ai_gov_map.summarise.backends.ollama_available", return_value=False), patch(
        "ai_gov_map.summarise.backends._hf_token", return_value=None
    ):
        # Force OllamaBackend init to fail by stubbing pick
        with patch(
            "ai_gov_map.summarise.backends.pick_ollama_model", return_value=None
        ), patch.dict("os.environ", {}, clear=False):
            # Clear HF tokens for this test
            with patch.dict(
                "os.environ",
                {"HF_TOKEN": "", "HUGGINGFACE_API_TOKEN": ""},
                clear=False,
            ):
                backend = resolve_backend("auto")
    assert isinstance(backend, OfflineBackend)


def test_ollama_requested_but_missing_raises():
    with patch(
        "ai_gov_map.summarise.backends.pick_ollama_model", return_value=None
    ):
        with pytest.raises(BackendError, match="Ollama"):
            resolve_backend("ollama")


def test_dry_run_writes_nothing(tmp_path: Path):
    csv_path = tmp_path / "regs.csv"
    out = tmp_path / "summaries.jsonl"
    write_csv(csv_path, [_rec(id="dry:1")])
    stats = run_summarise(csv_path, out, backend="offline", dry_run=True)
    assert stats["written"] == 0
    assert stats["pending"] == 1
    assert not out.exists()
