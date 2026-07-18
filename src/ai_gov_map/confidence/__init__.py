"""Phase 4 confidence / human-review heuristics → re-flag summaries.jsonl."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from ai_gov_map.ingest.normalize import read_csv
from ai_gov_map.summarise.models import SummaryRecord
from ai_gov_map.summarise.store import load_summaries, write_summaries

from .heuristics import (
    LOW_CONFIDENCE_THRESHOLD,
    detect_date_conflicts,
    detect_hedging,
    detect_low_confidence,
    detect_off_taxonomy,
    evaluate_summary,
)

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SUMMARIES = _REPO_ROOT / "data" / "summaries.jsonl"
DEFAULT_REGULATIONS = _REPO_ROOT / "data" / "regulation_data.csv"
DEFAULT_REVIEW_QUEUE = _REPO_ROOT / "data" / "review_queue.jsonl"


def apply_judgment(
    record: SummaryRecord,
    *,
    metadata_date: str | None = None,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
    preserve_backend_flag: bool = True,
) -> tuple[SummaryRecord, dict[str, Any]]:
    """Run heuristics and return an updated record plus the judgment dict.

    ``needs_review`` becomes True if heuristics fire, or (when
    ``preserve_backend_flag``) if the record was already flagged.
    """
    # Evaluate heuristics on content; ignore prior flag so reasons stay specific.
    probe = replace(record, needs_review=False)
    judgment = evaluate_summary(
        probe,
        metadata_date=metadata_date,
        low_confidence_threshold=low_confidence_threshold,
    )
    needs = bool(judgment["needs_human_review"])
    if preserve_backend_flag and record.needs_review:
        needs = True
        if not judgment["reasons"]:
            judgment = {
                **judgment,
                "needs_human_review": True,
                "reasons": ["backend already flagged needs_review"],
            }
        else:
            judgment = {**judgment, "needs_human_review": True}
    updated = replace(record, needs_review=needs)
    return updated, judgment


def run_reflag(
    summaries_path: Path | str | None = None,
    regulations_path: Path | str | None = None,
    *,
    review_queue_path: Path | str | None = None,
    write_queue: bool = False,
    dry_run: bool = False,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    """Re-evaluate existing summaries and refresh ``needs_review`` in place.

    Does **not** regenerate summary text. Optionally writes a companion
    ``review_queue.jsonl`` of ``{id, needs_human_review, reasons, risk_tier}``.
    """
    sum_path = Path(summaries_path) if summaries_path else DEFAULT_SUMMARIES
    reg_path = Path(regulations_path) if regulations_path else DEFAULT_REGULATIONS
    queue_path = Path(review_queue_path) if review_queue_path else DEFAULT_REVIEW_QUEUE

    dates: dict[str, str] = {}
    if reg_path.exists():
        for rec in read_csv(reg_path):
            if rec.id:
                dates[rec.id] = rec.date or ""

    records = load_summaries(sum_path)
    updated: list[SummaryRecord] = []
    queue_rows: list[dict[str, Any]] = []
    flagged = 0
    changed = 0

    for rec in records:
        new_rec, judgment = apply_judgment(
            rec,
            metadata_date=dates.get(rec.id),
            low_confidence_threshold=low_confidence_threshold,
            preserve_backend_flag=True,
        )
        if new_rec.needs_review:
            flagged += 1
        if new_rec.needs_review != rec.needs_review:
            changed += 1
        updated.append(new_rec)
        if judgment["needs_human_review"] or judgment["reasons"]:
            queue_rows.append(
                {
                    "id": rec.id,
                    "needs_human_review": judgment["needs_human_review"],
                    "reasons": judgment["reasons"],
                    "risk_tier": rec.risk_tier,
                    "confidence": rec.confidence,
                }
            )

    if dry_run:
        logger.info(
            "dry-run: would reflag %s summaries (%s flagged, %s changed) → %s",
            len(records),
            flagged,
            changed,
            sum_path,
        )
    else:
        write_summaries(sum_path, updated)
        logger.info(
            "Reflagged %s summaries (%s flagged, %s needs_review changed) → %s",
            len(updated),
            flagged,
            changed,
            sum_path,
        )
        if write_queue:
            queue_path.parent.mkdir(parents=True, exist_ok=True)
            with queue_path.open("w", encoding="utf-8") as fh:
                for row in queue_rows:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            logger.info("Wrote review queue (%s rows) → %s", len(queue_rows), queue_path)

    return {
        "total": len(records),
        "flagged": flagged,
        "changed": changed,
        "output": sum_path,
        "queue": queue_path if write_queue else None,
        "queue_rows": len(queue_rows),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai_gov_map.confidence",
        description=(
            "Phase 4 judgement heuristics: flag summaries that need human review "
            "(hedging, date conflicts, off-taxonomy tiers, low confidence). "
            "Re-flags existing summaries.jsonl without regenerating text."
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_SUMMARIES,
        help=f"Summaries JSONL (default: {DEFAULT_SUMMARIES})",
    )
    parser.add_argument(
        "--regulations",
        type=Path,
        default=DEFAULT_REGULATIONS,
        help=f"Regulation CSV for metadata dates (default: {DEFAULT_REGULATIONS})",
    )
    parser.add_argument(
        "--write-queue",
        action="store_true",
        help=f"Also write companion review queue ({DEFAULT_REVIEW_QUEUE.name})",
    )
    parser.add_argument(
        "--queue-output",
        type=Path,
        default=DEFAULT_REVIEW_QUEUE,
        help=f"Review queue path (default: {DEFAULT_REVIEW_QUEUE})",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=LOW_CONFIDENCE_THRESHOLD,
        help=f"Low-confidence threshold (default: {LOW_CONFIDENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate and print counts without writing",
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
    if not args.input.exists():
        print(f"Summaries file not found: {args.input}", file=sys.stderr)
        return 1
    stats = run_reflag(
        args.input,
        args.regulations,
        review_queue_path=args.queue_output,
        write_queue=args.write_queue,
        dry_run=args.dry_run,
        low_confidence_threshold=args.threshold,
    )
    print(
        f"Confidence reflag: total={stats['total']} flagged={stats['flagged']} "
        f"changed={stats['changed']} → {stats['output']}"
        + (
            f" queue={stats['queue_rows']}→{stats['queue']}"
            if stats.get("queue")
            else ""
        )
        + (" (dry-run)" if args.dry_run else "")
    )
    return 0


__all__ = [
    "DEFAULT_REGULATIONS",
    "DEFAULT_REVIEW_QUEUE",
    "DEFAULT_SUMMARIES",
    "LOW_CONFIDENCE_THRESHOLD",
    "apply_judgment",
    "detect_date_conflicts",
    "detect_hedging",
    "detect_low_confidence",
    "detect_off_taxonomy",
    "evaluate_summary",
    "main",
    "run_reflag",
]
