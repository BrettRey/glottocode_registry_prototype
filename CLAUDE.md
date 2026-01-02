# CLAUDE.md

This file provides guidance to Claude Code when working with this project.

## Project Overview

**Title:** Glottocode-first Registry Prototype
**Type:** Python/Web application
**Purpose:** Minimal, working prototype of a linguistic resource registry using Glottocodes as the primary identifier

## Architecture

```
glottocode_registry_prototype/
├── schema/
│   └── resource.schema.json    # JSON Schema for registry entries
├── data/
│   └── registry.jsonl          # Registry data (one JSON object per line)
├── scripts/
│   └── validate.py             # Schema validator
├── index.html                  # Static search UI
└── registry.json               # Built from registry.jsonl for web
```

## Key Design Choices

- **Glottocode required** - primary language identifier (from Glottolog)
- **Public-only for now** - access level must be open
- **Links required** - at least a landing page
- **Everything else optional** - cheap seeding

## Development Commands

```bash
# Validate registry
python scripts/validate.py

# Run quality checks (extra rules)
python scripts/quality.py data/registry.jsonl registry.json

# Build web registry JSON
python scripts/build_web_registry.py data/registry.jsonl registry.json

# Import CSV/TSV into JSONL
python scripts/import_registry.py path/to/input.csv data/registry.jsonl --append
python scripts/import_registry.py path/to/input.csv data/registry.jsonl --validate-schema

# Batch import pipeline
python scripts/batch_import.py path/to/input.csv data/registry.jsonl registry.json --append --schema schema/resource.schema.json

# Optional link check (networked)
python scripts/link_check.py data/registry.jsonl --limit 25

# Seed Common Voice entries (networked)
python scripts/generate_common_voice_entries.py data/registry.jsonl --count 100 --append

# Seed Language Science Press grammars (networked)
python scripts/generate_langsci_grammar_entries.py data/registry.jsonl --count 100 --append

# Run local server for web UI
python -m http.server 8000
```

## Workflow

1. Add/edit records in `data/registry.jsonl`
2. Run `scripts/validate.py` to check schema + validity
3. Build `registry.json` for the search UI

## Role: Developer

Claude's role in this project is **Developer** - can write code, modify schemas, add registry entries, and improve the prototype.

## Next Steps (from README)

- [ ] Add controlled vocabularies for annotation layers and formats
- [ ] Add automated link checking + `last_verified` stamp
- [ ] Add Glottolog validation step (ensure glottocode exists)
- [ ] Decide governance model
