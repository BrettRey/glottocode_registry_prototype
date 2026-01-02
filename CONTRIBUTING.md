# Contributing

Thanks for helping grow the glottocode-first registry! This project accepts **publicly accessible** resources only. We store metadata and links, not the data itself.

## What to Add
- Public corpora, lexicons, grammars, treebanks, datasets, tools, or bibliographies.
- A stable landing page and an explicit license.

## How to Add a Resource
1. Add a JSON object (one per line) to `data/registry.jsonl`.
2. Keep keys in the same order as `schema/resource.schema.json` for readability.
   - For batches, use the importer: `python scripts/import_registry.py input.csv data/registry.jsonl --append`
   - Schema enum validation: `python scripts/import_registry.py input.csv data/registry.jsonl --validate-schema`
   - Template CSV: `templates/registry_import_template.csv`
3. Regenerate `registry.json`:
   - `python scripts/build_web_registry.py data/registry.jsonl registry.json`
   - Or run the pipeline: `python scripts/batch_import.py input.csv data/registry.jsonl registry.json --append --schema schema/resource.schema.json`
4. Validate and run quality checks:
   - `python scripts/validate.py data/registry.jsonl schema/resource.schema.json`
   - `python scripts/quality.py data/registry.jsonl registry.json`

## Field Conventions
- `resource_id`: lowercase with hyphens (e.g., `example-treebank`).
- `glottocode`: 4 letters + 4 digits (e.g., `abcd1234`).
- `access.level`: must be `open`.
- `formats` and `annotation_layers`: use the controlled vocab in `schema/resource.schema.json`.
- `links`: include at least one `landing` URL (https preferred).

## Suggested Workflow
- Open an issue using the “Suggest a resource” template, or submit a PR directly.
- Add 10–30 entries per PR for reviewability.
