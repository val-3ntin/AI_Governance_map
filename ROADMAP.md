# Action Roadmap — AI-Powered Regulatory Compliance Monitor

**Repo:** [val-3ntin/AI_Governance_map](https://github.com/val-3ntin/AI_Governance_map)  
**End state:** complete, valuable, interview-ready project · public GitHub · live Streamlit site  
**Budget:** free/open-source only · **~6–9 weeks** part-time  

---

## Current baseline (as of main)

| Artifact | State | Gap |
|----------|--------|-----|
| `README.md` | One-line description | No problem statement, architecture, or demo link |
| `requirements.txt` | Unpinned (`streamlit`, `pandas`, …) | Fragile installs |
| `app.py` | ~1040-line Streamlit monolith; hardcoded actor/pillar matrix | Logic not reusable or testable |
| `italy_ai_governance_heatmap_v3.ipynb` | Primary research/logic notebook | Blocks “real package” credibility |
| Live demo | None (no homepage URL) | Recruiters cannot click anything |
| Ingestion / CI / tests / LLM / overrides | Absent | Entire Phases 1–6 |

**What already works and should be preserved:** Italy/EU framing, 12 actors × 5 pillars, decay scoring, Briefing / Stakeholder Map / Capacity Matrix / Decay Simulation / Playbooks UI.

**Rule:** Do not start Phase 1 until Phase 0 has a **live Streamlit URL**. A clean package + demo beats half-built APIs with no runnable app.

---

## Target architecture

```text
Free sources                Package                         Flat data (git)
─────────────               ─────────                       ───────────────
EUR-Lex  ─┐                 src/ai_gov_map/
OECD.AI  ─┼─► ingest.py  ──► data/raw/ + regulation_data.csv
AgID RSS ─┤                 scoring.py ──► scores.csv / history.json
Garante  ─┤                 summarise.py ─► summaries.jsonl (Ollama → HF fallback)
GDELT   ─┘                 match.py     ─► impact_flags.csv (entities.yaml)
                            confidence.py ► needs_human_review + overrides.json
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
     ingest.py      # stubs OK in P0; real clients in P1
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

## Phase 1 — Automate data ingestion (Weeks 2–3)

**Definition of done:** Monthly GitHub Action updates `data/regulation_data.csv`; run is green on `main`.

### Sources (all free)

| Source | Use | Notes |
|--------|-----|--------|
| EUR-Lex REST/SPARQL | Official EU AI Act text + amendments | Primary legal corpus |
| OECD.AI Policy Observatory API | National AI policy tracking | EU vs Italy comparison |
| AgID + Garante Privacy RSS | Italian institutional signals | No auth |
| GDELT | AI-governance news fallback | No key; noisy — filter hard |

### Tasks

1. Implement thin clients under `src/ai_gov_map/ingest/` (one module per source).
2. Normalise to a single schema, e.g.  
   `id, date, title, source, url, jurisdiction, text_excerpt, fetched_at`
3. Write `.github/workflows/ingest.yml` — `schedule: cron: '0 6 1 * *'` + `workflow_dispatch`.
4. Action: install deps → run `python -m ai_gov_map.ingest` → commit CSV if changed (or open a PR).
5. Document cadence in README (“refreshed monthly”).

### Acceptance checklist

- [ ] Dry-run locally produces valid CSV
- [ ] Action completes on public repo without secrets (or only optional HF token later)
- [ ] Existing heatmap still runs if ingest fails (graceful empty/new file)

---

## Phase 2 — LLM summarisation (Weeks 4–5)

**Definition of done:** Each new row can get `summary` + `risk_tier` ∈ {unacceptable, high, limited, minimal}.

### Tasks

1. `summarise.py` — primary: **Ollama** (Llama 3.1 8B or Mistral 7B); fallback: Hugging Face free Inference API.
2. Prompt: plain-language summary (≤120 words) + single risk tag + short rationale.
3. Idempotent: skip IDs already in `data/summaries.jsonl`.
4. Document: “Local open-weight by default; no paid API required.”

### Acceptance checklist

- [ ] Works offline with Ollama when available
- [ ] HF path documented for Streamlit Cloud / no local GPU
- [ ] Cloud deploy does not crash if Ollama absent (use cached summaries in git)

**Cloud note:** Prefer committing pre-computed summaries so the live site works without secrets; run LLM locally or in Actions when a token is present.

---

## Phase 3 — Entity tracking + compliance mapping (Week 6)

**Definition of done:** 5–8 tracked entities get impact flags per regulatory item via rules (no ML).

### Tasks

1. `data/entities.yaml` — sector, AI use-cases, keywords, optional risk exposure.
2. Rules matcher: keyword + taxonomy overlap → `data/impact_flags.csv`.
3. Stay flat-file only (`scores.csv`, `regulation_data.csv`, `history.json`, …).

### Acceptance checklist

- [ ] Matcher is deterministic and unit-tested
- [ ] Entities are clearly labelled hypothetical/anonymised if not real orgs

---

## Phase 4 — Judgement layer (Week 7) — **differentiator**

**Definition of done:** Auto “needs human review” + a filled override log you can show in interviews.

### Tasks

1. Confidence heuristics: hedging language (“may”, “unclear”), conflicting dates, tag outside taxonomy → `needs_human_review=true`.
2. Small UI or CLI to record override: previous tag, new tag, one-line reason → `data/overrides.json`.
3. Seed **5–10 real overrides** with honest reasoning (interview gold).

### Acceptance checklist

- [ ] Override log is in the repo and readable
- [ ] README links to 1–2 example overrides as “where the model was wrong”

---

## Phase 5 — Dashboard upgrade (Week 8)

**Definition of done:** Heatmap preserved; timeline + filters + export shipped.

### Tasks

1. Timeline of regulatory items over time (Plotly is already a dep).
2. Filter/search: tracked entities + risk tiers.
3. One-click CSV/JSON download of the filtered view.

### Acceptance checklist

- [ ] Existing Briefing / Map / Matrix pages still work
- [ ] Export matches what the filter shows

---

## Phase 6 — Testing & polish (Week 9, 3–5 days)

**Definition of done:** Repo looks finished to a recruiter skimming for 90 seconds.

### Tasks

1. **pytest** — 10–15 tests on ingest normalisation + scoring decay edge cases.
2. **CHANGELOG.md** — Keep a Changelog style.
3. **README (final)** — problem, architecture, screenshots/GIF, live demo, stack, limitations & what you’d improve.
4. Optional: GitHub Topics (`ai-governance`, `streamlit`, `eu-ai-act`, `italy`).

### Acceptance checklist

- [ ] `pytest` green in CI (optional workflow) or documented locally
- [ ] Limitations section is specific (not generic)

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
│   ├── scoring.py
│   ├── summarise.py
│   ├── match.py
│   ├── confidence.py
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

## This week — execute Phase 0 only

1. Extract `load_data` / `compute_scores` into `src/ai_gov_map/scoring.py`; dump matrix to `data/scores.csv`.  
2. Slim `app.py`; confirm local UI parity.  
3. Pin requirements; add minimal README.  
4. Deploy Streamlit Community Cloud; add live link.  
5. Open a `phase-1-ingest` branch only after the URL is live.

When Phase 0 is done, say the word and implementation can start on extraction + deploy step-by-step.
