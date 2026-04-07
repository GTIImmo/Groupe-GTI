Phase 1 SQL pipeline:

1. Probe the API quickly:
   `.\.venv\Scripts\python.exe probe_api.py --pretty`

2. Sync raw payloads into SQLite:
   `.\.venv\Scripts\python.exe sync_raw.py --max-pages 3 --detail-limit 50`

3. Normalize source tables:
   `.\.venv\Scripts\python.exe normalize_source.py`

4. Build the first consolidated dossier index:
   `.\.venv\Scripts\python.exe build_case_index.py`

5. Compare API totals vs raw stock vs normalized tables:
   `.\.venv\Scripts\python.exe check_global_gap.py`

Database location by default:
`data\hektor.sqlite`

Current SQL schema:
`sql\schema_phase1.sql`

Notes:
- `sync_raw.py` stores both listings and `ById` details for annonces, contacts, mandats, offres, compromis, and ventes.
- `normalize_source.py` prefers `ById` payloads when they are present because they are usually richer than listings.
- `normalize_source.py` also tries to relink mandats to annonces via `AnnonceById.mandats` and `NO_MANDAT` when `idAnnonce` is missing.
- the SQLite schema now includes indexes on the main join keys used by the dossier consolidation.
- `case_dossier_source` is a source-side consolidated view, not yet the final internal workflow model.
- `check_global_gap.py` provides a quick API vs RAW vs DATA comparison to measure global coverage after a sync or an update run.
- use `--max-pages 0` to fetch all available pages for a resource.
- use `--detail-limit 0` to fetch all available `ById` details for the synced listing IDs.

Recommended transaction-heavy sync:
`.\.venv\Scripts\python.exe sync_raw.py --resources offres compromis ventes --max-pages 0 --detail-limit 0 --no-with-offer-status --no-with-compromis-status --vente-date-start 2010-01-01 --vente-date-end 2030-12-31`
