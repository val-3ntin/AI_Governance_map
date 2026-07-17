"""Scheduled data ingestion clients (Phase 1).

Stubs only in Phase 0 — EUR-Lex, OECD.AI, AgID/Garante RSS, and GDELT
will land here and write to ``data/regulation_data.csv``.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = _REPO_ROOT / "data" / "regulation_data.csv"


def run_ingest(output_path: Path | str | None = None) -> Path:
    """Run all configured sources and write a normalised CSV.

    Phase 0: no-op that ensures the output path exists as an empty schema file
    if missing. Phase 1 replaces this with real clients.
    """
    path = Path(output_path) if output_path else DEFAULT_OUTPUT
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "id,date,title,source,url,jurisdiction,text_excerpt,fetched_at\n",
            encoding="utf-8",
        )
    return path
