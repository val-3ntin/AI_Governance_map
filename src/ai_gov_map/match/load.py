"""Load entities.yaml and optional summary risk tiers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from .models import Entity

logger = logging.getLogger(__name__)


def load_entities(path: Path | str) -> list[Entity]:
    """Parse ``entities.yaml``; returns entities in file order."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"entities file not found: {p}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if raw is None:
        return []
    if not isinstance(raw, dict):
        raise ValueError(f"entities.yaml root must be a mapping, got {type(raw).__name__}")

    meta = raw.get("meta") or {}
    hypothetical_default = bool(meta.get("hypothetical", True))
    items = raw.get("entities")
    if items is None:
        # Allow a bare list root for tests.
        raise ValueError("entities.yaml missing 'entities' list")
    if not isinstance(items, list):
        raise ValueError("'entities' must be a list")

    entities: list[Entity] = []
    seen: set[str] = set()
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"entities[{i}] must be a mapping")
        ent = Entity.from_mapping(item, hypothetical=hypothetical_default)
        if not ent.id:
            raise ValueError(f"entities[{i}] missing id")
        if ent.id in seen:
            raise ValueError(f"duplicate entity id: {ent.id}")
        seen.add(ent.id)
        entities.append(ent)
    logger.info("Loaded %s entities from %s", len(entities), p)
    return entities


def load_risk_tiers(path: Path | str | None) -> dict[str, str]:
    """Map regulation id → risk_tier from summaries.jsonl (optional)."""
    if path is None:
        return {}
    p = Path(path)
    if not p.is_file():
        logger.warning("summaries file not found (%s); risk_tier will be empty", p)
        return {}
    tiers: dict[str, str] = {}
    with p.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row: dict[str, Any] = json.loads(text)
            except json.JSONDecodeError:
                logger.warning("Skipping invalid JSONL at %s:%s", p, line_no)
                continue
            rid = str(row.get("id") or "").strip()
            tier = str(row.get("risk_tier") or "").strip().lower()
            if rid and tier:
                tiers[rid] = tier
    logger.info("Loaded %s risk tiers from %s", len(tiers), p)
    return tiers
