"""Summary record schema and EU AI Act risk taxonomy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

# Closed taxonomy — prompt + validators must use only these values.
RISK_TIERS: tuple[str, ...] = ("unacceptable", "high", "limited", "minimal")

SUMMARY_FIELDS: tuple[str, ...] = (
    "id",
    "summary",
    "risk_tier",
    "rationale",
    "model",
    "created_at",
    "confidence",
    "needs_review",
)


@dataclass(frozen=True)
class SummaryRecord:
    """One LLM (or offline) summary keyed by regulation ``id``."""

    id: str
    summary: str
    risk_tier: str
    rationale: str
    model: str
    created_at: str
    confidence: float = 0.5
    needs_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> SummaryRecord:
        needs = row.get("needs_review", False)
        if isinstance(needs, str):
            needs = needs.strip().lower() in {"1", "true", "yes", "y"}
        conf = row.get("confidence", 0.5)
        try:
            conf_f = float(conf)
        except (TypeError, ValueError):
            conf_f = 0.5
        return cls(
            id=str(row.get("id") or ""),
            summary=str(row.get("summary") or ""),
            risk_tier=str(row.get("risk_tier") or ""),
            rationale=str(row.get("rationale") or ""),
            model=str(row.get("model") or ""),
            created_at=str(row.get("created_at") or ""),
            confidence=conf_f,
            needs_review=bool(needs),
        )


def as_row(record: SummaryRecord) -> dict[str, Any]:
    return {f.name: getattr(record, f.name) for f in fields(record)}
