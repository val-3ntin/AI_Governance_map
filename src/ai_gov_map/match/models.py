"""Entity and impact-flag schemas for Phase 3 compliance mapping."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

IMPACT_FLAG_COLUMNS: tuple[str, ...] = (
    "regulation_id",
    "entity_id",
    "match_score",
    "matched_terms",
    "risk_tier",
    "reason",
    "flagged_at",
)

# Closed set aligned with Phase 2 summarise taxonomy (optional on flags).
RISK_TIERS: tuple[str, ...] = ("unacceptable", "high", "limited", "minimal")


@dataclass(frozen=True)
class Entity:
    """One tracked (often hypothetical) organisation profile."""

    id: str
    display_name: str
    sector: str
    ai_use_cases: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    risk_exposure: str = ""
    notes: str = ""
    hypothetical: bool = True

    @classmethod
    def from_mapping(cls, row: dict[str, Any], *, hypothetical: bool = True) -> Entity:
        use_cases = row.get("ai_use_cases") or []
        keywords = row.get("keywords") or []
        if isinstance(use_cases, str):
            use_cases = [use_cases]
        if isinstance(keywords, str):
            keywords = [keywords]
        return cls(
            id=str(row.get("id") or "").strip(),
            display_name=str(row.get("display_name") or "").strip(),
            sector=str(row.get("sector") or "").strip(),
            ai_use_cases=tuple(str(x).strip() for x in use_cases if str(x).strip()),
            keywords=tuple(str(x).strip() for x in keywords if str(x).strip()),
            risk_exposure=str(row.get("risk_exposure") or "").strip(),
            notes=str(row.get("notes") or "").strip(),
            hypothetical=bool(row.get("hypothetical", hypothetical)),
        )


@dataclass(frozen=True)
class ImpactFlag:
    """One entity ↔ regulation impact flag (rules-based)."""

    regulation_id: str
    entity_id: str
    match_score: float
    matched_terms: str
    risk_tier: str
    reason: str
    flagged_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "regulation_id": self.regulation_id,
            "entity_id": self.entity_id,
            "match_score": f"{self.match_score:.2f}",
            "matched_terms": self.matched_terms,
            "risk_tier": self.risk_tier,
            "reason": self.reason,
            "flagged_at": self.flagged_at,
        }

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> ImpactFlag:
        try:
            score = float(row.get("match_score") or 0)
        except (TypeError, ValueError):
            score = 0.0
        return cls(
            regulation_id=str(row.get("regulation_id") or ""),
            entity_id=str(row.get("entity_id") or ""),
            match_score=score,
            matched_terms=str(row.get("matched_terms") or ""),
            risk_tier=str(row.get("risk_tier") or ""),
            reason=str(row.get("reason") or ""),
            flagged_at=str(row.get("flagged_at") or ""),
        )


def as_row(flag: ImpactFlag) -> dict[str, str]:
    return flag.to_dict()


def entity_as_dict(entity: Entity) -> dict[str, Any]:
    return asdict(entity)
