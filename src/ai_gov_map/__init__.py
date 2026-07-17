"""Italy / EU AI governance capacity mapping and scoring."""

__version__ = "0.1.0"

from .scoring import (
    ACTIVITY_WEIGHTS,
    GROUP_COLORS,
    PILLARS,
    PILLAR_LABELS,
    compute_heatmap,
    compute_scores,
    load_data,
)

__all__ = [
    "ACTIVITY_WEIGHTS",
    "GROUP_COLORS",
    "PILLARS",
    "PILLAR_LABELS",
    "compute_heatmap",
    "compute_scores",
    "load_data",
    "__version__",
]
