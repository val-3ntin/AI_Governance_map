"""Shared dashboard helpers for the Streamlit UI.

Phase 0 keeps most page markup in ``app.py``. Chart builders and export
helpers will move here as Phase 5 grows the UI.
"""

from __future__ import annotations

from typing import Any


def filter_actors_by_group(
    actors: list[str],
    actor_meta: dict[str, dict[str, Any]],
    groups: list[str],
) -> list[str]:
    """Return actors whose group is in ``groups``."""
    return [a for a in actors if actor_meta[a]["group"] in groups]
