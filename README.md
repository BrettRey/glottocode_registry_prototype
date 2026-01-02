# Glottocode-first registry (prototype)

This is a minimal, working prototype of a Glottocode-first linguistic resource registry.

## What it is
- A **JSON Schema** describing a registry entry: `schema/resource.schema.json`
- A **JSONL registry** you can grow with one entry per line: `data/registry.jsonl`
- A tiny **validator**: `scripts/validate.py`
- A **quality checker** for extra rules: `scripts/quality.py`
- A single-file **search UI** you can open locally: `web/index.html` (loads `web/registry.json`)

## Design choices (minimal, pragmatic)
- **Glottocode is required** (primary language identifier).
- **Access is first-class** (open vs restricted/controlled/closed).
- **Links are required** (at least a landing page).
- Everything else is optional so seeding is cheap.

## Suggested workflow (GitHub-friendly)
1. Contributors add/edit records in `data/registry.jsonl` via PR.
2. CI runs `scripts/validate.py` to enforce schema + basic validity.
3. CI runs `scripts/quality.py` for duplicate IDs, landing links, and date sanity.
4. Periodic releases produce `web/registry.json` for the static search page.

## Next steps (if you want this to become real)
- Add controlled vocabularies for annotation layers and formats.
- Add automated link checking + a `last_verified` stamp.
- Add a Glottolog validation step (ensure glottocode exists).
- Decide governance: who can merge, how disputes are handled, how restricted resources are represented.
