"""JSON persistence for the human override log."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import OverrideRecord


def load_overrides(path: Path | str) -> list[OverrideRecord]:
    p = Path(path)
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "overrides" in raw:
        raw = raw["overrides"]
    if not isinstance(raw, list):
        raise ValueError(f"overrides file must be a JSON list: {p}")
    records: list[OverrideRecord] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"overrides[{i}] in {p} is not an object")
        records.append(OverrideRecord.from_mapping(item))
    return records


def write_overrides(path: Path | str, records: Iterable[OverrideRecord]) -> int:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = [r.to_dict() for r in records]
    p.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(rows)


def overrides_by_id(path: Path | str) -> dict[str, OverrideRecord]:
    """Latest override per document id (file order; last wins)."""
    by_id: dict[str, OverrideRecord] = {}
    for rec in load_overrides(path):
        if rec.id:
            by_id[rec.id] = rec
    return by_id
