"""Shared regulation record model and CSV schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

SCHEMA_COLUMNS: tuple[str, ...] = (
    "id",
    "date",
    "title",
    "source",
    "url",
    "jurisdiction",
    "text_excerpt",
    "fetched_at",
)


@dataclass(frozen=True)
class RegulationRecord:
    """Normalised regulatory / policy item."""

    id: str
    date: str
    title: str
    source: str
    url: str
    jurisdiction: str
    text_excerpt: str
    fetched_at: str

    def to_dict(self) -> dict[str, str]:
        return {f.name: str(getattr(self, f.name) or "") for f in fields(self)}

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> RegulationRecord:
        return cls(**{col: str(row.get(col) or "") for col in SCHEMA_COLUMNS})


def as_row(record: RegulationRecord) -> dict[str, str]:
    return asdict(record)
