"""Scheduled data ingestion — EUR-Lex, OECD.AI fallback, AgID/Garante RSS, GDELT."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from pathlib import Path

import requests

from .eurlex import fetch_ai_act_family
from .gdelt import fetch_gdelt
from .models import RegulationRecord
from .normalize import merge_records, read_csv, write_csv
from .oecd import fetch_oecd_comparison
from .rss_sources import fetch_agid, fetch_garante

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = _REPO_ROOT / "data" / "regulation_data.csv"
DEFAULT_RAW_DIR = _REPO_ROOT / "data" / "raw"

SOURCE_FETCHERS: dict[str, Callable[..., list[RegulationRecord]]] = {
    "eurlex": fetch_ai_act_family,
    "oecd": fetch_oecd_comparison,
    "agid": fetch_agid,
    "garante": fetch_garante,
    "gdelt": fetch_gdelt,
}

ALL_SOURCES = tuple(SOURCE_FETCHERS.keys())


def run_ingest(
    output_path: Path | str | None = None,
    *,
    sources: list[str] | None = None,
    raw_dir: Path | str | None = DEFAULT_RAW_DIR,
    session: requests.Session | None = None,
) -> Path:
    """Run selected sources, merge with existing CSV, write if we have data.

    Per-source failures are logged and skipped. If **all** sources fail and the
    output file already has rows, the existing file is left untouched.
    """
    path = Path(output_path) if output_path else DEFAULT_OUTPUT
    raw = Path(raw_dir) if raw_dir else None
    selected = list(sources) if sources else list(ALL_SOURCES)
    unknown = [s for s in selected if s not in SOURCE_FETCHERS]
    if unknown:
        raise ValueError(f"Unknown sources: {unknown}; choose from {list(ALL_SOURCES)}")

    existing = read_csv(path)
    sess = session or requests.Session()
    incoming: list[RegulationRecord] = []
    failures: list[str] = []

    for name in selected:
        fetcher = SOURCE_FETCHERS[name]
        try:
            batch = fetcher(session=sess, raw_dir=raw)
            incoming.extend(batch)
            logger.info("Source %s OK (%s records)", name, len(batch))
        except Exception as exc:  # noqa: BLE001 — isolate per-source failure
            failures.append(name)
            logger.exception("Source %s failed: %s", name, exc)

    if not incoming:
        if existing:
            logger.warning(
                "All sources failed or returned empty (%s); preserving existing CSV (%s rows)",
                failures or "none",
                len(existing),
            )
            return path
        # Bootstrap empty schema only when nothing exists yet
        path.parent.mkdir(parents=True, exist_ok=True)
        write_csv(path, [])
        logger.warning("No records available; wrote empty schema to %s", path)
        return path

    merged = merge_records(existing, incoming)
    write_csv(path, merged)
    logger.info(
        "Wrote %s records to %s (incoming=%s, existing=%s, failures=%s)",
        len(merged),
        path,
        len(incoming),
        len(existing),
        failures or "none",
    )
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ai_gov_map.ingest",
        description="Ingest free AI-governance sources into data/regulation_data.csv",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help=f"Directory for raw snapshots (default: {DEFAULT_RAW_DIR})",
    )
    parser.add_argument(
        "--no-raw",
        action="store_true",
        help="Do not write raw source snapshots",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=list(ALL_SOURCES),
        default=None,
        help=f"Subset of sources (default: all of {', '.join(ALL_SOURCES)})",
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
    raw_dir = None if args.no_raw else args.raw_dir
    out = run_ingest(args.output, sources=args.sources, raw_dir=raw_dir)
    print(f"Ingest complete: {out}")
    return 0


__all__ = [
    "ALL_SOURCES",
    "DEFAULT_OUTPUT",
    "DEFAULT_RAW_DIR",
    "run_ingest",
    "main",
]
