"""Phase 4 human override log → data/overrides.json (+ effective_tier helper)."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from ai_gov_map.summarise.models import RISK_TIERS
from ai_gov_map.summarise.store import load_summaries

from .models import OverrideRecord, validate_tier
from .store import load_overrides, overrides_by_id, write_overrides

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OVERRIDES = _REPO_ROOT / "data" / "overrides.json"
DEFAULT_SUMMARIES = _REPO_ROOT / "data" / "summaries.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def effective_tier(
    doc_id: str,
    *,
    overrides_path: Path | str | None = None,
    summaries_path: Path | str | None = None,
    summary_tier: str | None = None,
    overrides_index: dict[str, OverrideRecord] | None = None,
) -> str | None:
    """Return the override tier if present, else the summary tier.

    Readable helper for Phase 5 dashboard wiring. Pass ``summary_tier`` or
    ``summaries_path`` to resolve the fallback; returns ``None`` if unknown.
    """
    oid = (doc_id or "").strip()
    if not oid:
        return None

    index = overrides_index
    if index is None:
        path = Path(overrides_path) if overrides_path else DEFAULT_OVERRIDES
        index = overrides_by_id(path) if path.exists() else {}

    if oid in index:
        return index[oid].new_tier

    if summary_tier is not None:
        return (summary_tier or "").strip().lower() or None

    sum_path = Path(summaries_path) if summaries_path else DEFAULT_SUMMARIES
    if sum_path.exists():
        # Last record for id wins (JSONL may theoretically duplicate under --force).
        found: str | None = None
        for rec in load_summaries(sum_path):
            if rec.id == oid:
                found = rec.risk_tier
        return (found or "").strip().lower() or None
    return None


def add_override(
    *,
    doc_id: str,
    previous_tier: str,
    new_tier: str,
    reason: str,
    overrides_path: Path | str | None = None,
    overridden_by: str = "",
    overridden_at: str | None = None,
    replace_existing: bool = True,
) -> OverrideRecord:
    """Append (or replace) an override and persist ``overrides.json``."""
    path = Path(overrides_path) if overrides_path else DEFAULT_OVERRIDES
    prev = validate_tier(previous_tier, field="previous_tier")
    nxt = validate_tier(new_tier, field="new_tier")
    reason_clean = (reason or "").strip()
    if not reason_clean:
        raise ValueError("reason is required (one-line interview-ready note)")
    if not (doc_id or "").strip():
        raise ValueError("id is required")

    record = OverrideRecord(
        id=doc_id.strip(),
        previous_tier=prev,
        new_tier=nxt,
        reason=reason_clean,
        overridden_at=overridden_at or _utc_now(),
        overridden_by=(overridden_by or "").strip(),
    )

    existing = load_overrides(path)
    if replace_existing:
        existing = [r for r in existing if r.id != record.id]
    existing.append(record)
    write_overrides(path, existing)
    logger.info(
        "Override recorded: %s %s → %s (%s)",
        record.id,
        record.previous_tier,
        record.new_tier,
        path,
    )
    return record


def list_overrides(
    overrides_path: Path | str | None = None,
) -> list[OverrideRecord]:
    path = Path(overrides_path) if overrides_path else DEFAULT_OVERRIDES
    return load_overrides(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai_gov_map.overrides",
        description=(
            "Human risk-tier override log (Phase 4). "
            "Stores corrections in data/overrides.json for dashboard use."
        ),
    )
    parser.add_argument(
        "-o",
        "--overrides",
        type=Path,
        default=DEFAULT_OVERRIDES,
        help=f"Overrides JSON path (default: {DEFAULT_OVERRIDES})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Record a tier override with a one-line reason")
    add_p.add_argument("--id", required=True, help="Regulation / summary document id")
    add_p.add_argument(
        "--from",
        dest="previous_tier",
        required=True,
        choices=RISK_TIERS,
        help="Previous (model/rules) risk tier",
    )
    add_p.add_argument(
        "--to",
        dest="new_tier",
        required=True,
        choices=RISK_TIERS,
        help="Corrected risk tier",
    )
    add_p.add_argument("--reason", required=True, help="One-line reason for the override")
    add_p.add_argument(
        "--by",
        dest="overridden_by",
        default="",
        help="Optional reviewer name / handle",
    )
    add_p.add_argument(
        "--keep-history",
        action="store_true",
        help="Append even if an override for this id already exists (default: replace)",
    )

    list_p = sub.add_parser("list", help="List overrides in the log")
    list_p.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON instead of a table",
    )

    eff = sub.add_parser(
        "effective",
        help="Resolve effective_tier(id) = override if present else summary tier",
    )
    eff.add_argument("--id", required=True, help="Document id")
    eff.add_argument(
        "--summaries",
        type=Path,
        default=DEFAULT_SUMMARIES,
        help=f"Summaries JSONL (default: {DEFAULT_SUMMARIES})",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.command == "add":
        try:
            rec = add_override(
                doc_id=args.id,
                previous_tier=args.previous_tier,
                new_tier=args.new_tier,
                reason=args.reason,
                overrides_path=args.overrides,
                overridden_by=args.overridden_by,
                replace_existing=not args.keep_history,
            )
        except ValueError as exc:
            print(f"Override failed: {exc}", file=sys.stderr)
            return 1
        print(
            f"Recorded override: {rec.id} {rec.previous_tier} → {rec.new_tier}\n"
            f"  reason: {rec.reason}\n"
            f"  → {args.overrides}"
        )
        return 0

    if args.command == "list":
        rows = list_overrides(args.overrides)
        if args.json:
            import json

            print(json.dumps([r.to_dict() for r in rows], ensure_ascii=False, indent=2))
            return 0
        if not rows:
            print(f"No overrides in {args.overrides}")
            return 0
        print(f"{len(rows)} override(s) in {args.overrides}\n")
        for r in rows:
            who = f" by {r.overridden_by}" if r.overridden_by else ""
            print(
                f"- {r.id}: {r.previous_tier} → {r.new_tier}{who}\n"
                f"    {r.reason}\n"
                f"    @ {r.overridden_at}"
            )
        return 0

    if args.command == "effective":
        tier = effective_tier(
            args.id,
            overrides_path=args.overrides,
            summaries_path=args.summaries,
        )
        if tier is None:
            print(f"No tier found for id={args.id!r}", file=sys.stderr)
            return 1
        print(tier)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


__all__ = [
    "DEFAULT_OVERRIDES",
    "DEFAULT_SUMMARIES",
    "OverrideRecord",
    "RISK_TIERS",
    "add_override",
    "effective_tier",
    "list_overrides",
    "load_overrides",
    "main",
    "overrides_by_id",
    "write_overrides",
]
