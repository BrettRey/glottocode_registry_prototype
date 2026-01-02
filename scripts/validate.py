#!/usr/bin/env python3
"""
Validate registry JSONL entries against the JSON Schema.

Usage:
  python scripts/validate.py data/registry.jsonl schema/resource.schema.json
"""
import json, sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Missing dependency: jsonschema. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

def main(registry_path: Path, schema_path: Path) -> int:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    ok = True
    for i, line in enumerate(registry_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"[line {i}] JSON decode error: {e}", file=sys.stderr)
            ok = False
            continue

        errors = sorted(validator.iter_errors(rec), key=lambda e: list(e.path))
        if errors:
            ok = False
            print(f"[line {i}] resource_id={rec.get('resource_id','<missing>')}", file=sys.stderr)
            for e in errors:
                path = ".".join([str(p) for p in e.path]) if e.path else "<root>"
                print(f"  - {path}: {e.message}", file=sys.stderr)

    if ok:
        print("OK: all entries validate.")
        return 0
    return 1

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
