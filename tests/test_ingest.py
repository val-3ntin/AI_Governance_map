"""Phase 1 ingest: normalisation, parsers, error isolation (mocked HTTP)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from ai_gov_map.ingest import run_ingest
from ai_gov_map.ingest.eurlex import fetch_ai_act_family
from ai_gov_map.ingest.gdelt import fetch_gdelt
from ai_gov_map.ingest.models import SCHEMA_COLUMNS, RegulationRecord
from ai_gov_map.ingest.normalize import (
    clean_text,
    dedupe_records,
    make_record,
    merge_records,
    normalize_url,
    parse_date,
    read_csv,
    write_csv,
)
from ai_gov_map.ingest.oecd import fetch_oecd_comparison
from ai_gov_map.ingest.rss_sources import _parse_feed


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test</title>
    <item>
      <title>Intelligenza artificiale: linee guida AgID</title>
      <link>https://www.agid.gov.it/it/notizie/ai-linee-guida</link>
      <pubDate>Mon, 01 Jul 2024 10:00:00 +0000</pubDate>
      <description>Consulta pubblica sulle linee guida IA per la PA.</description>
    </item>
    <item>
      <title>Webinar su open data</title>
      <link>https://www.agid.gov.it/it/notizie/open-data</link>
      <pubDate>Tue, 02 Jul 2024 10:00:00 +0000</pubDate>
      <description>Evento generico su cataloghi e riuso dei dati pubblici.</description>
    </item>
  </channel>
</rss>
"""

SPARQL_JSON = {
    "results": {
        "bindings": [
            {
                "celex": {"value": "32024R1689"},
                "date": {"value": "2024-06-13"},
                "title": {
                    "value": "Regulation (EU) 2024/1689 of the European Parliament"
                },
            },
            {
                "celex": {"value": "32024R1689R(01)"},
                "date": {"value": "2024-07-01"},
            },
        ]
    }
}

GDELT_JSON = {
    "articles": [
        {
            "url": "https://example.com/eu-ai-act-passes",
            "title": "EU AI Act enters into force",
            "seendate": "20240715T120000Z",
            "domain": "example.com",
            "language": "English",
        },
        {
            "url": "https://example.com/sports",
            "title": "Local football results",
            "seendate": "20240715T130000Z",
            "domain": "example.com",
            "language": "English",
        },
    ]
}


def test_schema_columns_match_model():
    assert SCHEMA_COLUMNS == (
        "id",
        "date",
        "title",
        "source",
        "url",
        "jurisdiction",
        "text_excerpt",
        "fetched_at",
    )
    rec = make_record(
        source="Test",
        title="Hello",
        url="https://Example.com/Path/",
        jurisdiction="EU",
        date="2024-06-13T12:00:00Z",
        text_excerpt="<b>Excerpt</b>  text",
    )
    assert rec.date == "2024-06-13"
    assert rec.url == "https://example.com/Path"
    assert "<" not in rec.text_excerpt
    assert set(rec.to_dict()) == set(SCHEMA_COLUMNS)


def test_parse_date_variants():
    assert parse_date("2024-06-13") == "2024-06-13"
    assert parse_date("20240715T120000Z") == "2024-07-15"
    assert parse_date("Mon, 01 Jul 2024 10:00:00 +0000") == "2024-07-01"
    assert parse_date("") == ""
    assert parse_date(None) == ""


def test_dedupe_and_merge_deterministic(tmp_path: Path):
    a = make_record(
        source="A",
        title="One",
        url="https://ex.com/1",
        jurisdiction="EU",
        date="2024-01-01",
        record_id="id:1",
        fetched_at="2024-01-01T00:00:00Z",
    )
    b = make_record(
        source="A",
        title="One again",
        url="https://ex.com/1",
        jurisdiction="EU",
        date="2024-01-02",
        record_id="id:1",
        fetched_at="2024-02-01T00:00:00Z",
    )
    c = make_record(
        source="B",
        title="Two",
        url="https://ex.com/2",
        jurisdiction="Italy",
        date="2023-01-01",
        record_id="id:2",
        fetched_at="2024-01-01T00:00:00Z",
    )
    merged = merge_records([a, c], [b])
    assert len(merged) == 2
    by_id = {r.id: r for r in merged}
    assert by_id["id:1"].title == "One again"
    assert by_id["id:1"].fetched_at == "2024-02-01T00:00:00Z"
    # Deterministic order: newest date first
    assert merged[0].id == "id:1"
    out = tmp_path / "out.csv"
    write_csv(out, merged)
    roundtrip = read_csv(out)
    assert [r.id for r in roundtrip] == [r.id for r in merged]


def test_rss_ai_keyword_filter():
    records = _parse_feed(
        SAMPLE_RSS,
        source="AgID",
        jurisdiction="Italy",
        fetched_at="2024-07-01T00:00:00Z",
    )
    assert len(records) == 1
    assert "intelligenza artificiale" in records[0].title.lower()
    assert records[0].date == "2024-07-01"


def test_eurlex_sparql_parser():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = json.dumps(SPARQL_JSON)
    mock_resp.raise_for_status = MagicMock()
    sess = MagicMock()
    sess.post.return_value = mock_resp
    records = fetch_ai_act_family(session=sess, raw_dir=None)
    assert len(records) == 2
    assert records[0].id == "eurlex:32024R1689"
    assert records[0].source == "EUR-Lex"
    assert "32024R1689" in records[0].url
    assert records[0].jurisdiction == "EU"


def test_gdelt_hard_filter():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = json.dumps(GDELT_JSON)
    with patch("ai_gov_map.ingest.gdelt.get_text", return_value=(mock_resp.text, mock_resp)):
        records = fetch_gdelt(session=MagicMock(), raw_dir=None)
    assert len(records) == 1
    assert "AI Act" in records[0].title
    assert records[0].date == "2024-07-15"


def test_oecd_curated_without_live_ping():
    records = fetch_oecd_comparison(verify_live=False, raw_dir=None)
    assert len(records) >= 2
    assert all(r.source == "OECD.AI" for r in records)
    assert any("italy" in r.url.lower() for r in records)


def test_run_ingest_preserves_csv_on_total_failure(tmp_path: Path):
    out = tmp_path / "regulation_data.csv"
    seed = [
        RegulationRecord(
            id="keep:1",
            date="2024-01-01",
            title="Seed",
            source="Seed",
            url="https://example.com/seed",
            jurisdiction="EU",
            text_excerpt="do not wipe",
            fetched_at="2024-01-01T00:00:00Z",
        )
    ]
    write_csv(out, seed)

    def boom(**_kwargs):
        raise RuntimeError("network down")

    import ai_gov_map.ingest as ingest_mod

    original = dict(ingest_mod.SOURCE_FETCHERS)
    try:
        for key in list(ingest_mod.SOURCE_FETCHERS):
            ingest_mod.SOURCE_FETCHERS[key] = boom
        result = run_ingest(out, raw_dir=None)
    finally:
        ingest_mod.SOURCE_FETCHERS.clear()
        ingest_mod.SOURCE_FETCHERS.update(original)

    assert result == out
    kept = read_csv(out)
    assert len(kept) == 1
    assert kept[0].id == "keep:1"
    assert kept[0].text_excerpt == "do not wipe"


def test_dedupe_drops_duplicate_urls():
    a = make_record(
        source="A",
        title="T1",
        url="https://ex.com/x",
        jurisdiction="EU",
        record_id="a",
        date="2024-01-01",
    )
    b = make_record(
        source="B",
        title="T2",
        url="https://ex.com/x",
        jurisdiction="EU",
        record_id="b",
        date="2024-02-01",
    )
    out = dedupe_records([a, b])
    assert len(out) == 1
    assert out[0].id == "a"


def test_clean_text_strips_html_and_truncates():
    long = "<p>" + ("word " * 300) + "</p>"
    cleaned = clean_text(long, max_len=40)
    assert "<" not in cleaned
    assert len(cleaned) <= 40
    assert cleaned.endswith("…")


def test_normalize_url_lowercases_and_strips_slash():
    assert normalize_url("HTTPS://Example.COM/Path/") == "https://example.com/Path"
    assert normalize_url("") == ""
    assert normalize_url(None) == ""


def test_merge_empty_incoming_preserves_existing():
    existing = [
        make_record(
            source="Seed",
            title="Keep",
            url="https://ex.com/keep",
            jurisdiction="EU",
            record_id="keep:1",
            date="2024-01-01",
            fetched_at="2024-01-01T00:00:00Z",
        )
    ]
    merged = merge_records(existing, [])
    assert len(merged) == 1
    assert merged[0].id == "keep:1"
