## Summary

## Checklist
- [ ] Added/updated entries in `data/registry.jsonl`
- [ ] Regenerated `web/registry.json` (if data changed)
- [ ] `python scripts/validate.py data/registry.jsonl schema/resource.schema.json`
- [ ] `python scripts/quality.py data/registry.jsonl web/registry.json`
- [ ] Confirmed access level is `open` and license is present
- [ ] Included a UI screenshot if `web/index.html` changed
