"""JSONL persistence for document summaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import SummaryRecord


def load_summaries(path: Path | str) -> list[SummaryRecord]:
    p = Path(path)
    if not p.exists():
        return []
    records: list[SummaryRecord] = []
    with p.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {p}:{line_no}: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL line {line_no} in {p} is not an object")
            records.append(SummaryRecord.from_mapping(obj))
    return records


def known_ids(path: Path | str) -> set[str]:
    return {r.id for r in load_summaries(path) if r.id}


def append_summaries(path: Path | str, records: Iterable[SummaryRecord]) -> int:
    """Append summary records as JSONL lines. Returns count written."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with p.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
            count += 1
    return count


def write_summaries(path: Path | str, records: Iterable[SummaryRecord]) -> int:
    """Overwrite JSONL with the given records (deterministic order preserved)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = list(records)
    with p.open("w", encoding="utf-8") as fh:
        for rec in rows:
            fh.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
    return len(rows)
