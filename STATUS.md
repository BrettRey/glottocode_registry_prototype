# Glottocode Registry Prototype

**Status:** Initial prototype
**Last Updated:** Jan 1, 2026

---

## Project Summary

Minimal, working prototype of a Glottocode-first linguistic resource registry. Uses Glottocodes (from Glottolog) as the primary language identifier, with access level as a first-class field.

---

## Current State

- [x] JSON Schema defined (`schema/resource.schema.json`)
- [x] JSONL registry format (`data/registry.jsonl`)
- [x] Validator script (`scripts/validate.py`)
- [x] Static search UI (`web/index.html`)
- [ ] Controlled vocabularies for annotation layers/formats
- [ ] Automated link checking
- [ ] Glottolog validation (verify glottocodes exist)
- [ ] Governance model

---

## Files

| File | Purpose |
|------|---------|
| `schema/resource.schema.json` | JSON Schema for registry entries |
| `data/registry.jsonl` | Registry data (one entry per line) |
| `scripts/validate.py` | Schema validator |
| `web/index.html` | Static search UI |
| `web/registry.json` | Built registry for web |

---

## Session Log

- **2026-01-01**: Project added to portfolio. AI coordination files created (CLAUDE.md, STATUS.md).
