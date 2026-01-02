# Repository Guidelines

## Project Structure & Module Organization
- `schema/resource.schema.json`: JSON Schema for registry entries.
- `data/registry.jsonl`: Registry data; one JSON object per line.
- `scripts/validate.py`: JSON Schema validator for registry entries.
- `scripts/quality.py`: Data quality checks beyond schema validation.
- `web/index.html`: Static search UI.
- `web/registry.json`: JSON array consumed by the UI; keep it in sync with `data/registry.jsonl`.
- `README.md`, `STATUS.md`, `CLAUDE.md`: Project context and workflow notes.

## Build, Test, and Development Commands
- Validate registry data:
  - `python scripts/validate.py data/registry.jsonl schema/resource.schema.json`
  - Fails on schema errors; prints line numbers and paths.
- Run quality checks:
  - `python scripts/quality.py data/registry.jsonl web/registry.json`
  - Checks duplicates, landing links, date ordering, and web registry sync.
- Serve the UI locally:
  - `python -m http.server 8000 --directory web`
  - Then open `http://localhost:8000` in a browser.
- There is no build step; updates to `web/registry.json` are manual.

## Coding Style & Naming Conventions
- Python: 4-space indentation, standard library style, keep scripts small and readable.
- JSON Schema: 2-space indentation; do not add fields outside the schema (`additionalProperties: false`).
- JSONL entries: one line per record; keep keys in schema order for readability.
- Field naming: `resource_id` is lowercase with hyphens (e.g., `example-treebank`); `glottocode` is 4 letters + 4 digits.

## Testing Guidelines
- No unit test framework is currently configured.
- Run the validator after any data or schema change.
- If you edit the UI, verify it renders and filters against `web/registry.json`.

## Commit & Pull Request Guidelines
- No Git history is present in this directory, so there is no established commit convention.
- Suggested commit style: short imperative summaries (e.g., "Add corpus entry for X", "Tighten schema for links").
- PRs should include: a brief description, the affected entries or schema changes, and validation output. Include a UI screenshot if `web/index.html` changes.

## Dependencies & Local Setup
- Requires Python 3 and the `jsonschema` package (`pip install jsonschema`).
- Keep `web/registry.json` aligned with `data/registry.jsonl` before sharing or releasing.
