"""Rules-based entity ↔ regulation impact matcher → data/impact_flags.csv."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ai_gov_map.ingest.normalize import read_csv

from .load import load_entities, load_risk_tiers
from .matcher import MIN_SCORE, match_all
from .models import IMPACT_FLAG_COLUMNS, Entity, ImpactFlag
from .store import read_impact_flags, write_impact_flags

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENTITIES = _REPO_ROOT / "data" / "entities.yaml"
DEFAULT_REGULATIONS = _REPO_ROOT / "data" / "regulation_data.csv"
DEFAULT_SUMMARIES = _REPO_ROOT / "data" / "summaries.jsonl"
DEFAULT_OUTPUT = _REPO_ROOT / "data" / "impact_flags.csv"


def run_match(
    entities_path: Path | str | None = None,
    regulations_path: Path | str | None = None,
    summaries_path: Path | str | None = None,
    output_path: Path | str | None = None,
    *,
    min_score: float = MIN_SCORE,
    flagged_at: str | None = None,
    dry_run: bool = False,
    skip_summaries: bool = False,
) -> dict[str, int | Path | float]:
    """Load inputs, match, and rewrite impact_flags.csv.

    Returns stats: ``flags``, ``entities``, ``regulations``, ``output``.
    """
    ent_path = Path(entities_path) if entities_path else DEFAULT_ENTITIES
    reg_path = Path(regulations_path) if regulations_path else DEFAULT_REGULATIONS
    out_path = Path(output_path) if output_path else DEFAULT_OUTPUT
    sum_path: Path | None
    if skip_summaries:
        sum_path = None
    elif summaries_path is not None:
        sum_path = Path(summaries_path)
    else:
        sum_path = DEFAULT_SUMMARIES

    entities = load_entities(ent_path)
    regulations = read_csv(reg_path)
    risk_tiers = load_risk_tiers(sum_path)

    flags = match_all(
        entities,
        regulations,
        risk_tiers=risk_tiers,
        flagged_at=flagged_at,
        min_score=min_score,
    )

    if dry_run:
        logger.info(
            "dry-run: would write %s flags (%s entities × %s regulations) → %s",
            len(flags),
            len(entities),
            len(regulations),
            out_path,
        )
        return {
            "flags": len(flags),
            "entities": len(entities),
            "regulations": len(regulations),
            "output": out_path,
            "min_score": min_score,
        }

    write_impact_flags(out_path, flags)
    return {
        "flags": len(flags),
        "entities": len(entities),
        "regulations": len(regulations),
        "output": out_path,
        "min_score": min_score,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai_gov_map.match",
        description=(
            "Rules-based keyword/taxonomy matcher: map hypothetical entities "
            "in entities.yaml onto regulation_data.csv → impact_flags.csv. "
            "Deterministic full rewrite (no ML / no network)."
        ),
    )
    parser.add_argument(
        "--entities",
        type=Path,
        default=DEFAULT_ENTITIES,
        help=f"entities.yaml (default: {DEFAULT_ENTITIES})",
    )
    parser.add_argument(
        "-i",
        "--regulations",
        type=Path,
        default=DEFAULT_REGULATIONS,
        help=f"regulation CSV (default: {DEFAULT_REGULATIONS})",
    )
    parser.add_argument(
        "--summaries",
        type=Path,
        default=DEFAULT_SUMMARIES,
        help=f"summaries JSONL for risk_tier (default: {DEFAULT_SUMMARIES})",
    )
    parser.add_argument(
        "--skip-summaries",
        action="store_true",
        help="Do not load summaries.jsonl (risk_tier column left empty)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=MIN_SCORE,
        help=f"Minimum match_score to emit a flag (default: {MIN_SCORE})",
    )
    parser.add_argument(
        "--flagged-at",
        type=str,
        default=None,
        help=(
            "Override flagged_at for all rows (ISO-8601). "
            "Default: each regulation's fetched_at (deterministic)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute flags without writing the CSV",
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
        stats = run_match(
            args.entities,
            args.regulations,
            None if args.skip_summaries else args.summaries,
            args.output,
            min_score=args.min_score,
            flagged_at=args.flagged_at,
            dry_run=args.dry_run,
            skip_summaries=args.skip_summaries,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        logger.error("%s", exc)
        print(f"Match failed: {exc}", file=sys.stderr)
        return 1
    mode = "dry-run" if args.dry_run else "wrote"
    print(
        f"Match complete ({mode}): flags={stats['flags']} "
        f"entities={stats['entities']} regulations={stats['regulations']} "
        f"→ {stats['output']}"
    )
    return 0


__all__ = [
    "DEFAULT_ENTITIES",
    "DEFAULT_OUTPUT",
    "DEFAULT_REGULATIONS",
    "DEFAULT_SUMMARIES",
    "IMPACT_FLAG_COLUMNS",
    "Entity",
    "ImpactFlag",
    "MIN_SCORE",
    "load_entities",
    "load_risk_tiers",
    "main",
    "match_all",
    "read_impact_flags",
    "run_match",
    "write_impact_flags",
]
