"""LLM / offline summarisation of regulation feed rows → data/summaries.jsonl."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from ai_gov_map.ingest.models import RegulationRecord
from ai_gov_map.ingest.normalize import read_csv

from .backends import (
    BackendError,
    OfflineBackend,
    SummariseBackend,
    resolve_backend,
)
from .models import RISK_TIERS, SummaryRecord
from .store import append_summaries, known_ids, load_summaries

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = _REPO_ROOT / "data" / "regulation_data.csv"
DEFAULT_OUTPUT = _REPO_ROOT / "data" / "summaries.jsonl"

BACKEND_CHOICES = ("auto", "ollama", "hf", "offline")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def summarise_record(
    record: RegulationRecord,
    backend: SummariseBackend,
    *,
    created_at: str | None = None,
) -> SummaryRecord:
    # Lazy import avoids circular load: confidence → summarise.models → summarise package.
    from ai_gov_map.confidence import apply_judgment

    result = backend.summarise(record)
    draft = SummaryRecord(
        id=record.id,
        summary=str(result["summary"]),
        risk_tier=str(result["risk_tier"]),
        rationale=str(result["rationale"]),
        model=str(result.get("model") or backend.name),
        created_at=created_at or _utc_now(),
        confidence=float(result.get("confidence", 0.5)),
        needs_review=bool(result.get("needs_review", False)),
    )
    # Phase 4: merge backend flag with confidence heuristics (hedging, dates, taxonomy).
    judged, judgment = apply_judgment(draft, metadata_date=record.date)
    if judgment.get("reasons"):
        logger.debug(
            "Judgement for %s: needs_review=%s reasons=%s",
            judged.id,
            judged.needs_review,
            judgment["reasons"],
        )
    return judged


def run_summarise(
    input_path: Path | str | None = None,
    output_path: Path | str | None = None,
    *,
    backend: str = "auto",
    force: bool = False,
    limit: int | None = None,
    dry_run: bool = False,
    session: requests.Session | None = None,
    backend_instance: SummariseBackend | None = None,
) -> dict[str, int | Path]:
    """Summarise new CSV rows and append to JSONL.

    Returns stats: ``{"written": n, "skipped": n, "total_input": n, "output": Path}``.
    """
    csv_path = Path(input_path) if input_path else DEFAULT_INPUT
    jsonl_path = Path(output_path) if output_path else DEFAULT_OUTPUT

    records = read_csv(csv_path)
    existing = set() if force else known_ids(jsonl_path)
    pending = [r for r in records if r.id and r.id not in existing]
    skipped = len(records) - len(pending)
    if limit is not None:
        pending = pending[: max(0, limit)]

    if not pending:
        logger.info(
            "Nothing to summarise (%s input rows, %s already known)",
            len(records),
            skipped,
        )
        return {
            "written": 0,
            "skipped": skipped,
            "total_input": len(records),
            "output": jsonl_path,
        }

    engine = backend_instance or resolve_backend(backend, session=session)
    logger.info(
        "Using backend=%s for %s new document(s) (skipped=%s)",
        engine.name,
        len(pending),
        skipped,
    )

    if dry_run:
        for rec in pending:
            logger.info("dry-run would summarise id=%s title=%s", rec.id, rec.title[:80])
        return {
            "written": 0,
            "skipped": skipped,
            "total_input": len(records),
            "output": jsonl_path,
            "pending": len(pending),
        }

    written_recs: list[SummaryRecord] = []
    for rec in pending:
        try:
            summary = summarise_record(rec, engine)
        except BackendError:
            raise
        except Exception as exc:  # noqa: BLE001 — isolate per-doc; fall back offline
            logger.exception("Summarise failed for %s (%s); using offline stub", rec.id, exc)
            summary = summarise_record(rec, OfflineBackend())
        written_recs.append(summary)
        logger.info(
            "Summarised %s → risk_tier=%s needs_review=%s",
            summary.id,
            summary.risk_tier,
            summary.needs_review,
        )

    n = append_summaries(jsonl_path, written_recs)
    logger.info("Appended %s summaries to %s", n, jsonl_path)
    return {
        "written": n,
        "skipped": skipped,
        "total_input": len(records),
        "output": jsonl_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai_gov_map.summarise",
        description=(
            "Summarise regulation_data.csv rows with Ollama (primary), "
            "Hugging Face Inference API (fallback), or offline rules. "
            "Writes/appends data/summaries.jsonl; skips known IDs."
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input CSV (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSONL (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--backend",
        choices=BACKEND_CHOICES,
        default="auto",
        help="Backend preference (default: auto = ollama → hf → offline)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-summarise even if id already exists in the JSONL (appends duplicates)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of new documents to summarise this run",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List pending IDs without calling a backend or writing",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Debug logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        stats = run_summarise(
            args.input,
            args.output,
            backend=args.backend,
            force=args.force,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    except BackendError as exc:
        logger.error("%s", exc)
        print(f"Summarise failed: {exc}", file=sys.stderr)
        return 1
    print(
        f"Summarise complete: written={stats['written']} "
        f"skipped={stats['skipped']} input={stats['total_input']} "
        f"→ {stats['output']}"
        + (f" pending={stats['pending']}" if "pending" in stats else "")
    )
    return 0


__all__ = [
    "BACKEND_CHOICES",
    "DEFAULT_INPUT",
    "DEFAULT_OUTPUT",
    "RISK_TIERS",
    "SummaryRecord",
    "load_summaries",
    "main",
    "run_summarise",
    "summarise_record",
]
