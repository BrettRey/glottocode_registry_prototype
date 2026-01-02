# Glottocode-first registry (prototype)

This is a minimal, working prototype of a Glottocode-first linguistic resource registry.
See `CONTRIBUTING.md` for how to add public resources.

## What it is
- A **JSON Schema** describing a registry entry: `schema/resource.schema.json`
- A **JSONL registry** you can grow with one entry per line: `data/registry.jsonl`
- A tiny **validator**: `scripts/validate.py`
- A **quality checker** for extra rules: `scripts/quality.py`
- A **builder** for the web registry: `scripts/build_web_registry.py`
- A **CSV/TSV importer** for batch seeding: `scripts/import_registry.py`
- A starter CSV template: `templates/registry_import_template.csv`
- A single-file **search UI** you can open locally: `web/index.html` (loads `web/registry.json`)

## Design choices (minimal, pragmatic)
- **Glottocode is required** (primary language identifier).
- **Public-only for now** (access level must be `open`).
- **Links are required** (at least a landing page).
- Everything else is optional so seeding is cheap.

## Suggested workflow (GitHub-friendly)
1. Contributors add/edit records in `data/registry.jsonl` via PR.
2. Regenerate `web/registry.json` with `scripts/build_web_registry.py`.
3. CI runs `scripts/validate.py` to enforce schema + basic validity.
4. CI runs `scripts/quality.py` for duplicate IDs, landing links, and date sanity.
5. Periodic releases publish the static search page.

## Next steps (if you want this to become real)
- Add automated link checking + a `last_verified` stamp.
- Add a Glottolog validation step (ensure glottocode exists).
- Decide governance: who can merge, how disputes are handled, how restricted resources are represented.
