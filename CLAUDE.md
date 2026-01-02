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
└── web/
    ├── index.html              # Static search UI
    └── registry.json           # Built from registry.jsonl for web
```

## Key Design Choices

- **Glottocode required** - primary language identifier (from Glottolog)
- **Access is first-class** - open/restricted/controlled/closed
- **Links required** - at least a landing page
- **Everything else optional** - cheap seeding

## Development Commands

```bash
# Validate registry
python scripts/validate.py

# Run quality checks (extra rules)
python scripts/quality.py data/registry.jsonl web/registry.json

# Build web registry JSON
python scripts/build_web_registry.py data/registry.jsonl web/registry.json

# Optional link check (networked)
python scripts/link_check.py data/registry.jsonl --limit 25

# Run local server for web UI
python -m http.server 8000 --directory web
```

## Workflow

1. Add/edit records in `data/registry.jsonl`
2. Run `scripts/validate.py` to check schema + validity
3. Build `web/registry.json` for the search UI

## Role: Developer

Claude's role in this project is **Developer** - can write code, modify schemas, add registry entries, and improve the prototype.

## Next Steps (from README)

- [ ] Add controlled vocabularies for annotation layers and formats
- [ ] Add automated link checking + `last_verified` stamp
- [ ] Add Glottolog validation step (ensure glottocode exists)
- [ ] Decide governance model
