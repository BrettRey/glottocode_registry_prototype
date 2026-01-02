#!/usr/bin/env python3
"""
Build web/registry.json from JSONL registry data.

Usage:
  python scripts/build_web_registry.py data/registry.jsonl web/registry.json
  python scripts/build_web_registry.py data/registry.jsonl web/registry.json --check
"""
import json
import sys
from pathlib import Path


def load_jsonl(path: Path):
    items = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"[line {i}] JSON decode error: {exc}")
    return items


def main(registry_path: Path, output_path: Path, check: bool) -> int:
    try:
        items = load_jsonl(registry_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if check:
        if not output_path.exists():
            print(f"Missing output file: {output_path}", file=sys.stderr)
            return 1
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Output JSON decode error: {exc}", file=sys.stderr)
            return 1
        if existing != items:
            print("web registry is out of sync with JSONL", file=sys.stderr)
            return 1
        print("OK: web registry is in sync.")
        return 0

    output_path.write_text(json.dumps(items, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) not in {2, 3}:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    registry = Path(args[0])
    output = Path(args[1])
    check = len(args) == 3 and args[2] == "--check"
    if len(args) == 3 and not check:
        print("Unknown option. Use --check.", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(registry, output, check))
