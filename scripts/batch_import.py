#!/usr/bin/env python3
"""
Batch import pipeline: CSV/TSV -> JSONL -> web registry -> validate -> quality.

Usage:
  python scripts/batch_import.py input.csv data/registry.jsonl registry.json
  python scripts/batch_import.py input.csv data/registry.jsonl registry.json --append --schema schema/resource.schema.json
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch import pipeline for registry.")
    parser.add_argument("input", help="CSV/TSV input file")
    parser.add_argument("output_jsonl", help="Output JSONL file (typically data/registry.jsonl)")
    parser.add_argument("output_web", help="Output web JSON (typically registry.json)")
    parser.add_argument("--append", action="store_true", help="Append to output JSONL")
    parser.add_argument("--schema", help="Path to JSON schema for enum validation")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_jsonl = Path(args.output_jsonl)
    output_web = Path(args.output_web)

    import_cmd = [sys.executable, "scripts/import_registry.py", str(input_path), str(output_jsonl)]
    if args.append:
        import_cmd.append("--append")
    if args.schema:
        import_cmd.extend(["--schema", args.schema])

    build_cmd = [
        sys.executable,
        "scripts/build_web_registry.py",
        str(output_jsonl),
        str(output_web),
    ]
    validate_cmd = [
        sys.executable,
        "scripts/validate.py",
        str(output_jsonl),
        "schema/resource.schema.json",
    ]
    quality_cmd = [
        sys.executable,
        "scripts/quality.py",
        str(output_jsonl),
        str(output_web),
    ]

    try:
        run(import_cmd)
        run(build_cmd)
        run(validate_cmd)
        run(quality_cmd)
    except subprocess.CalledProcessError as exc:
        return exc.returncode

    print("OK: batch import pipeline completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
