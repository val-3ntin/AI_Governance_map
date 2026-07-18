# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Streamlit Community Cloud live demo URL in README + GitHub About
- Merge Phase 1–6 branch stack to `main`; enable monthly ingest Action on public `main`

## [0.2.0] — 2026-07-18

Recruiting-ready monitor stack: ingest → summarise → match → judgement → Regulatory Feed, plus docs polish.

### Added

#### Phase 0 — Package baseline
- `src/ai_gov_map/` package with `scoring.py` extracted from the Streamlit monolith
- Flat capacity data in `data/scores.csv` + `data/actors.csv`
- Pinned `requirements.txt` / `requirements-dev.txt` and editable install via `pyproject.toml`
- Initial pytest suite for scoring smoke checks

#### Phase 1 — Free-source ingest
- Clients for EUR-Lex SPARQL, OECD.AI curated pages, AgID/Garante RSS, GDELT Doc 2.0
- Normalised schema → `data/regulation_data.csv` (+ raw dumps under `data/raw/`)
- CLI: `python -m ai_gov_map.ingest`
- Monthly GitHub Action (`.github/workflows/ingest.yml`) with `workflow_dispatch`

#### Phase 2 — LLM summarisation
- `ai_gov_map.summarise` with Ollama → Hugging Face → offline-rules backends
- Idempotent JSONL store `data/summaries.jsonl` (seeded for Cloud/demo)
- Closed risk taxonomy: `unacceptable` | `high` | `limited` | `minimal`

#### Phase 3 — Entity impact flags
- Hypothetical entity profiles in `data/entities.yaml`
- Rules-based matcher → `data/impact_flags.csv`
- CLI: `python -m ai_gov_map.match`

#### Phase 4 — Judgement layer
- Confidence heuristics (`needs_review`) via `python -m ai_gov_map.confidence`
- Human override log `data/overrides.json` + `python -m ai_gov_map.overrides`
- Seeded honest disagreement examples for interview walkthroughs

#### Phase 5 — Regulatory Feed
- Streamlit **Regulatory Feed** page: Plotly timeline, entity/tier/search filters, CSV/JSON export
- Pure helpers in `dashboard.py` (no Streamlit import in unit-tested path)

#### Phase 6 — Testing & polish
- Expanded pytest coverage (ingest normalisation + scoring decay edge cases)
- This CHANGELOG; final README (problem, architecture, commands, limitations)
- Optional CI workflow running `pytest` on push/PR

### Changed
- README rewritten for recruiter skim: problem → architecture → run → limitations
- ROADMAP checkboxes updated through Phase 6 (live demo URL still open)

### Notes on commit history
Phase 0 lands on `main`. Phases 1–6 were built as a local branch stack
(`phase1-ingest-*` → `phase2-summarise` → … → `phase6-polish`) without rewriting
earlier commits. Open Phase 1 PRs on GitHub should be merged carefully; later
phases are local until pushed.

## [0.1.0] — 2026-07

### Added
- Phase 0 consolidation: package layout, CSV capacity matrix, basic tests, v1 README

[Unreleased]: https://github.com/val-3ntin/AI_Governance_map/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/val-3ntin/AI_Governance_map/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/val-3ntin/AI_Governance_map/releases/tag/v0.1.0
