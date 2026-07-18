"""Override log schema for human risk-tier corrections."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

from ai_gov_map.summarise.models import RISK_TIERS

OVERRIDE_FIELDS: tuple[str, ...] = (
    "id",
    "previous_tier",
    "new_tier",
    "reason",
    "overridden_at",
    "overridden_by",
)


@dataclass(frozen=True)
class OverrideRecord:
    """One human override of a summary risk tier."""

    id: str
    previous_tier: str
    new_tier: str
    reason: str
    overridden_at: str
    overridden_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not data.get("overridden_by"):
            # Keep optional field out of seed JSON when empty? Prefer stable schema.
            pass
        return data

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> OverrideRecord:
        return cls(
            id=str(row.get("id") or ""),
            previous_tier=str(row.get("previous_tier") or ""),
            new_tier=str(row.get("new_tier") or ""),
            reason=str(row.get("reason") or ""),
            overridden_at=str(row.get("overridden_at") or ""),
            overridden_by=str(row.get("overridden_by") or ""),
        )


def validate_tier(tier: str, *, field: str = "tier") -> str:
    cleaned = (tier or "").strip().lower()
    if cleaned not in RISK_TIERS:
        raise ValueError(
            f"{field} must be one of {list(RISK_TIERS)}; got {tier!r}"
        )
    return cleaned


def as_row(record: OverrideRecord) -> dict[str, Any]:
    return {f.name: getattr(record, f.name) for f in fields(record)}
