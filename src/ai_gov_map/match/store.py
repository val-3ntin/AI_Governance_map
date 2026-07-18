"""CSV I/O for impact_flags.csv."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from .models import IMPACT_FLAG_COLUMNS, ImpactFlag

logger = logging.getLogger(__name__)


def write_impact_flags(path: Path | str, flags: list[ImpactFlag]) -> int:
    """Full rewrite of impact_flags.csv (deterministic column order)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(IMPACT_FLAG_COLUMNS))
        writer.writeheader()
        for flag in flags:
            writer.writerow(flag.to_dict())
    logger.info("Wrote %s impact flags to %s", len(flags), p)
    return len(flags)


def read_impact_flags(path: Path | str) -> list[ImpactFlag]:
    p = Path(path)
    if not p.is_file():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return [ImpactFlag.from_mapping(row) for row in reader]
