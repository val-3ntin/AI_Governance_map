"""EUR-Lex / Cellar client for the EU AI Act and related CELEX family."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from .http_util import HttpError
from .models import RegulationRecord
from .normalize import make_record, utc_now_iso

logger = logging.getLogger(__name__)

SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
EURLEX_TXT = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}"
# AI Act OJ regulation + corrigenda / related CELEX ids sharing the stem
AI_ACT_CELEX_PREFIX = "32024R1689"

SPARQL_AI_ACT = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT DISTINCT ?celex ?date ?title WHERE {
  ?work cdm:resource_legal_id_celex ?celex .
  FILTER(STRSTARTS(STR(?celex), "32024R1689"))
  OPTIONAL { ?work cdm:work_date_document ?date }
  OPTIONAL {
    ?exp cdm:expression_belongs_to_work ?work .
    ?exp cdm:expression_title ?title .
    FILTER(lang(?title) = "en" || lang(?title) = "")
  }
}
ORDER BY ?celex
LIMIT 50
""".strip()


def _binding_value(binding: dict[str, Any], key: str) -> str:
    node = binding.get(key) or {}
    return str(node.get("value") or "")


def fetch_ai_act_family(
    *,
    session: requests.Session | None = None,
    raw_dir: Path | None = None,
) -> list[RegulationRecord]:
    """Query Cellar SPARQL for CELEX 32024R1689* and normalise records."""
    fetched_at = utc_now_iso()
    sess = session or requests.Session()
    last_exc: Exception | None = None
    text = ""
    resp: requests.Response | None = None
    for attempt in range(1, 4):
        try:
            resp = sess.post(
                SPARQL_ENDPOINT,
                data={"query": SPARQL_AI_ACT},
                headers={
                    "Accept": "application/sparql-results+json",
                    "User-Agent": "AI-Gov-Map/0.1 (+https://github.com/val-3ntin/AI_Governance_map; research ingest)",
                },
                timeout=60,
            )
            if resp.status_code == 429 and attempt < 3:
                import time

                time.sleep(2.0 * attempt)
                continue
            resp.raise_for_status()
            text = resp.text
            break
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < 3:
                import time

                time.sleep(2.0 * attempt)
                continue
            raise HttpError(f"EUR-Lex SPARQL failed: {exc}") from exc
    else:
        raise HttpError(f"EUR-Lex SPARQL failed: {last_exc}")

    if raw_dir is not None:
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "eurlex_sparql_ai_act.json").write_text(text, encoding="utf-8")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        code = resp.status_code if resp is not None else "?"
        raise HttpError(f"EUR-Lex SPARQL returned non-JSON (HTTP {code})") from exc

    bindings = payload.get("results", {}).get("bindings", [])
    records: list[RegulationRecord] = []
    seen: set[str] = set()
    for b in bindings:
        celex = _binding_value(b, "celex")
        if not celex or celex in seen:
            continue
        seen.add(celex)
        title = _binding_value(b, "title") or f"EU legal act {celex}"
        date = _binding_value(b, "date")
        url = EURLEX_TXT.format(celex=celex)
        excerpt = (
            f"EUR-Lex / Cellar metadata for CELEX {celex} "
            f"(EU AI Act family, Regulation (EU) 2024/1689)."
        )
        records.append(
            make_record(
                source="EUR-Lex",
                title=title,
                url=url,
                jurisdiction="EU",
                date=date,
                text_excerpt=excerpt,
                record_id=f"eurlex:{celex}",
                fetched_at=fetched_at,
            )
        )
    logger.info("EUR-Lex: %s records", len(records))
    return records
