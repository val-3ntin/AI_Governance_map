# Raw ingest snapshots (Phase 1)

This directory holds **transient** responses from free sources during
`python -m ai_gov_map.ingest`:

| File | Source |
|------|--------|
| `eurlex_sparql_ai_act.json` | Cellar SPARQL (EU AI Act CELEX family) |
| `oecd_curated_fallback.txt` | OECD.AI fallback ping notes |
| `agid_rss.xml` | AgID RSS |
| `garante_rss.xml` | Garante Privacy RSS |
| `gdelt_doc.json` | GDELT Doc 2.0 ArtList |

Snapshots are useful for debugging; large JSON/XML files are gitignored.
Keep this README (and optionally tiny fixtures) under version control.
