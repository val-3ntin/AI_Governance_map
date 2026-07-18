# Action Roadmap — AI-Powered Regulatory Compliance Monitor

**Repo:** [val-3ntin/AI_Governance_map](https://github.com/val-3ntin/AI_Governance_map)  
**End state:** complete, valuable, interview-ready project · public GitHub · live Streamlit site  
**Budget:** free/open-source only · **~6–9 weeks** part-time  

---

## Current baseline (as of `phase6-polish`)

| Artifact | State | Gap |
|----------|--------|-----|
| `README.md` | Problem, architecture, commands, limitations | Live demo URL still a placeholder |
| `CHANGELOG.md` | Keep a Changelog covering Phases 0–6 | Tag `v0.2.0` when merging to `main` |
| `requirements.txt` | Pinned | — |
| Package + CLIs | ingest / summarise / match / confidence / overrides | Merge branch stack to `main` |
| Tests + CI | ≥50 pytest; `.github/workflows/ci.yml` | Green on GitHub after first push |
| Live demo | Not deployed | Streamlit Community Cloud (manual) |

**What already works and should be preserved:** Italy/EU framing, 12 actors × 5 pillars, decay scoring, Briefing / Stakeholder Map / Capacity Matrix / Decay Simulation / Playbooks / Regulatory Feed UI.

---

## Target architecture

```text
Free sources                Package                         Flat data (git)
─────────────               ─────────                       ───────────────
EUR-Lex  ─┐                 src/ai_gov_map/
OECD.AI* ─┼─► ingest/   ──► data/raw/ + regulation_data.csv
AgID RSS ─┤                 scoring.py ──► scores.csv / history.json
Garante  ─┤                 summarise.py ─► summaries.jsonl (Ollama → HF fallback)
GDELT   ─┘                 match/       ─► impact_flags.csv (entities.yaml)
  *curated fallback (no public API)
                            confidence/ ► needs_human_review + overrides.json
                                   │
                                   ▼
                            dashboard.py ◄── app.py (thin)
                                   │
                                   ▼
                         Streamlit Community Cloud (live)
                                   ▲
                         GitHub Actions (monthly cron)
```

---

## Phase 0 — Consolidate & de-risk (Week 1) — **START HERE**

**Definition of done:** `pip install -r requirements.txt && streamlit run app.py` works from a clean clone; public Streamlit URL in README + GitHub About.

### Tasks

1. **Package structure**
   ```text
   src/ai_gov_map/
     __init__.py
     ingest/       # Phase 1 — EUR-Lex / OECD / RSS / GDELT clients + CLI
     scoring.py     # extract compute_scores + weights
     dashboard.py   # page helpers / chart builders used by app.py
   data/
     scores.csv     # actor × pillar matrix (move out of Python literals)
   tests/           # empty or 1 smoke test
   ```
2. **Thin `app.py`** — Streamlit entry + navigation only; import from package.
3. **Pin `requirements.txt`** — e.g. `streamlit==1.x`, `pandas==2.x`, `plotly==5.x`, …; add optional `[dev]` or `requirements-dev.txt` with `pytest`.
4. **README (v1)** — one-paragraph problem, architecture diagram (mermaid or ASCII), local run steps.
5. **Deploy** — Streamlit Community Cloud → connect this repo → main → `app.py`. Paste URL into README and repo homepage.

### Acceptance checklist

- [x] Notebook is no longer the runtime path (can keep as `notebooks/` archive)
- [ ] Live demo URL works without local setup *(deploy to Streamlit Community Cloud)*
- [x] Scoring behaviour matches current app (spot-check heatmap numbers)

---

## Phase 1 — Automate data ingestion (Weeks 2–3) — **IMPLEMENTED (local)**

**Definition of done:** Monthly GitHub Action updates `data/regulation_data.csv`; run is green on `main`.

### Sources (all free)

| Source | Use | Notes |
|--------|-----|--------|
| EUR-Lex Cellar SPARQL | Official EU AI Act text + corrigenda (`32024R1689*`) | Primary legal corpus → `data/raw/` |
| OECD.AI Policy Observatory | EU vs Italy comparison | **No stable public API** — curated public-page fallback documented in `ingest/oecd.py` |
| AgID + Garante Privacy RSS | Italian institutional signals | No auth |
| GDELT Doc 2.0 | AI-governance news fallback | No key; noisy — hard-filtered; may 429 |

### Tasks

1. ~~Implement thin clients under `src/ai_gov_map/ingest/` (one module per source).~~
2. ~~Normalise to a single schema~~  
   `id, date, title, source, url, jurisdiction, text_excerpt, fetched_at`
3. ~~Write `.github/workflows/ingest.yml` — `schedule: cron: '0 6 1 * *'` + `workflow_dispatch`.~~
4. ~~Action: install deps → run `python -m ai_gov_map.ingest` → commit CSV if changed.~~
5. ~~Document cadence in README (“refreshed monthly”).~~

### Acceptance checklist

- [x] Dry-run locally produces valid CSV (`python -m ai_gov_map.ingest`)
- [ ] Action completes on public repo without secrets *(enable after merge to `main`; workflow is present)*
- [x] Existing heatmap still runs if ingest fails (per-source isolation; never wipe CSV on total failure)

---

## Phase 2 — LLM summarisation (Weeks 4–5) — **IMPLEMENTED (local)**

**Definition of done:** Each new row can get `summary` + `risk_tier` ∈ {unacceptable, high, limited, minimal}.

### Tasks

1. ~~`src/ai_gov_map/summarise/` — primary: **Ollama** (Llama 3.1 8B or Mistral 7B); fallback: Hugging Face free Inference API; offline rules for CI/Cloud.~~
2. ~~Prompt: plain-language summary (≤120 words) + single risk tag + short rationale.~~
3. ~~Idempotent: skip IDs already in `data/summaries.jsonl`.~~
4. ~~Document: “Local open-weight by default; no paid API required.”~~
5. ~~Seed `data/summaries.jsonl` for existing regulation rows (offline backend).~~

### Acceptance checklist

- [x] Works offline with Ollama when available (`--backend ollama|auto`)
- [x] HF path documented for Streamlit Cloud / no local GPU (`HF_TOKEN` / `HUGGINGFACE_API_TOKEN`)
- [x] Cloud deploy does not crash if Ollama absent (use cached `data/summaries.jsonl` in git; `--backend offline`)

**Cloud note:** Prefer committing pre-computed summaries so the live site works without secrets; run LLM locally or in Actions when a token is present. CLI: `python -m ai_gov_map.summarise`.

---

## Phase 3 — Entity tracking + compliance mapping (Week 6) — **IMPLEMENTED (local)**

**Definition of done:** 5–8 tracked entities get impact flags per regulatory item via rules (no ML).

### Tasks

1. ~~`data/entities.yaml` — sector, AI use-cases, keywords, optional risk exposure.~~
2. ~~Rules matcher: keyword + taxonomy overlap → `data/impact_flags.csv`.~~
3. ~~Stay flat-file only (`scores.csv`, `regulation_data.csv`, `summaries.jsonl`, `entities.yaml`, `impact_flags.csv`, …).~~

### Acceptance checklist

- [x] Matcher is deterministic and unit-tested
- [x] Entities are clearly labelled hypothetical/anonymised if not real orgs

**CLI:** `python -m ai_gov_map.match` (rewrites `data/impact_flags.csv`; optional `--summaries` for `risk_tier`).

---

## Phase 4 — Judgement layer (Week 7) — **IMPLEMENTED (local)**

**Definition of done:** Auto “needs human review” + a filled override log you can show in interviews.

### Tasks

1. ~~Confidence heuristics: hedging language (“may”, “unclear”), conflicting dates, tag outside taxonomy → `needs_human_review=true`.~~
2. ~~CLI to record override: previous tag, new tag, one-line reason → `data/overrides.json`.~~
3. ~~Seed **5–10 real overrides** with honest reasoning (interview gold).~~

### Acceptance checklist

- [x] Override log is in the repo and readable (`data/overrides.json`)
- [x] README links to 1–2 example overrides as “where the model was wrong”

**CLI:** `python -m ai_gov_map.confidence` (re-flag summaries) · `python -m ai_gov_map.overrides add|list|effective`

---

## Phase 5 — Dashboard upgrade (Week 8) — **IMPLEMENTED (local)**

**Definition of done:** Heatmap preserved; timeline + filters + export shipped.

### Tasks

1. ~~Timeline of regulatory items over time (Plotly is already a dep).~~
2. ~~Filter/search: tracked entities + risk tiers.~~
3. ~~One-click CSV/JSON download of the filtered view.~~

### Acceptance checklist

- [x] Existing Briefing / Map / Matrix pages still work
- [x] Export matches what the filter shows
- [x] New **Regulatory Feed** nav page (timeline + table + CSV/JSON download)
- [x] Helpers in `src/ai_gov_map/dashboard.py`; pytest covers filter/export

**UI:** Streamlit sidebar → **Regulatory Feed**  
**Helpers:** `build_monitor_frame` · `filter_monitor` · `dataframe_to_csv` / `dataframe_to_json` · `build_timeline_figure`

---

## Phase 6 — Testing & polish (Week 9, 3–5 days) — **IMPLEMENTED (local)**

**Definition of done:** Repo looks finished to a recruiter skimming for 90 seconds.

### Tasks

1. ~~**pytest** — ingest normalisation + scoring decay edge cases (suite ≥50).~~
2. ~~**CHANGELOG.md** — Keep a Changelog style (Phases 0–6).~~
3. ~~**README (final)** — problem, architecture, screenshots/GIF placeholder, live demo placeholder, stack, limitations & what you’d improve.~~
4. ~~Optional: GitHub Topics suggestion in README (`ai-governance`, `streamlit`, `eu-ai-act`, `italy`, …).~~
5. ~~Optional: `.github/workflows/ci.yml` runs `pytest` on push/PR.~~

### Acceptance checklist

- [x] `pytest` green locally; CI workflow present (`.github/workflows/ci.yml`)
- [x] Limitations section is specific (not generic)
- [ ] Screenshots/GIF committed under `docs/` *(after Cloud deploy or local capture)*
- [ ] Live demo URL pasted into README + GitHub About *(Streamlit Community Cloud)*

---

## Suggested target tree (end state)

```text
AI_Governance_map/
├── README.md
├── ROADMAP.md
├── CHANGELOG.md
├── requirements.txt
├── requirements-dev.txt
├── app.py
├── .streamlit/config.toml
├── .github/workflows/ingest.yml
├── .github/workflows/ci.yml
├── data/
│   ├── scores.csv
│   ├── regulation_data.csv
│   ├── summaries.jsonl
│   ├── entities.yaml
│   ├── impact_flags.csv
│   ├── history.json
│   └── overrides.json
├── notebooks/          # archived exploratory work
├── src/ai_gov_map/
│   ├── ingest/
│   ├── summarise/      # Phase 2 — Ollama / HF / offline → summaries.jsonl
│   ├── match/          # Phase 3 — entities.yaml → impact_flags.csv
│   ├── confidence/     # Phase 4 — needs_human_review heuristics
│   ├── overrides/      # Phase 4 — overrides.json + effective_tier
│   ├── scoring.py
│   └── dashboard.py
└── tests/
```

---

## “Complete project” gate (all must be true)

1. Clean clone → install → `streamlit run app.py` works.  
2. Public **Streamlit** URL linked from README.  
3. Ingest Action green within the last ~31 days (or clear manual refresh docs).  
4. At least one LLM summary path documented; cached summaries visible in the UI.  
5. `overrides.json` with real disagreement examples.  
6. pytest + CHANGELOG + honest limitations section.

---

## This week — Phase 6 shipped locally; remaining manual

1. ~~Extract scoring + data load into `src/`; pin deps; README.~~ (Phase 0 on `main`)  
2. ~~Ingest package + monthly workflow + tests.~~ (Phase 1 branches / PRs)  
3. ~~LLM summarisation (Ollama / HF / offline) + seeded `summaries.jsonl`.~~ (Phase 2 on `phase2-summarise`)  
4. ~~Entity profiles + rules matcher → `impact_flags.csv`.~~ (Phase 3 on `phase3-entities`)  
5. ~~Confidence heuristics + override log (`overrides.json`).~~ (Phase 4 on `phase4-judgement`)  
6. ~~Timeline + filters + export (**Regulatory Feed** page).~~ (Phase 5 on `phase5-dashboard`)  
7. ~~Pytest polish, CHANGELOG, final README, CI workflow.~~ (Phase 6 on `phase6-polish`)  
8. **Manual:** merge PR stack carefully (Phase 1 open PRs #1/#2 exist; Phases 2–6 are local) — do not force-push.  
9. **Manual:** push phase branches / open PRs when ready; enable ingest Action on `main`.  
10. **Manual:** deploy Streamlit Community Cloud; paste live URL + add screenshots.  
11. **Manual:** set GitHub Topics from the README suggestion list.

Phases 0–6 code is complete locally; the “complete project” gate still needs the live URL + a green ingest run on public `main`.
