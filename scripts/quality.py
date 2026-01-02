#!/usr/bin/env python3
"""
Data quality checks for registry entries beyond JSON Schema validation.
Public-only policy is enforced here (access level must be open).

Usage:
  python scripts/quality.py data/registry.jsonl [web/registry.json]
"""
import json
import sys
from datetime import date
from pathlib import Path


def load_jsonl(path: Path):
    items = []
    errors = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            items.append((i, json.loads(line)))
        except json.JSONDecodeError as exc:
            errors.append(f"[line {i}] JSON decode error: {exc}")
    return items, errors


def parse_date(value, field, line):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"[line {line}] invalid date for {field}: {value}")


def duplicates(values):
    seen = set()
    dupes = []
    for value in values:
        if value in seen:
            dupes.append(value)
        seen.add(value)
    return dupes


def main(registry_path: Path, web_path: Path | None = None) -> int:
    entries, parse_errors = load_jsonl(registry_path)
    errors = list(parse_errors)
    warnings = []

    resource_ids = set()

    for line, item in entries:
        resource_id = item.get("resource_id")
        if resource_id:
            if resource_id in resource_ids:
                errors.append(f"[line {line}] duplicate resource_id: {resource_id}")
            resource_ids.add(resource_id)

        links = item.get("links", [])
        if links:
            has_landing = any(link.get("kind") == "landing" for link in links if isinstance(link, dict))
            if not has_landing:
                errors.append(f"[line {line}] missing landing link")
            for link in links:
                url = link.get("url", "") if isinstance(link, dict) else ""
                if url and not url.startswith("https://"):
                    warnings.append(f"[line {line}] non-https link: {url}")
        else:
            errors.append(f"[line {line}] missing links array")

        access = item.get("access", {})
        level = access.get("level")
        if level and level != "open":
            errors.append(f"[line {line}] access level is not public: {level}")
        if level in {"restricted", "controlled", "closed"}:
            if not access.get("contact"):
                warnings.append(f"[line {line}] access level '{level}' missing contact")
            if not access.get("constraints"):
                warnings.append(f"[line {line}] access level '{level}' missing constraints")

        try:
            created = parse_date(item.get("created"), "created", line)
            updated = parse_date(item.get("updated"), "updated", line)
            if created and updated and updated < created:
                errors.append(f"[line {line}] updated precedes created")
            last_verified = parse_date(
                item.get("provenance", {}).get("last_verified"),
                "provenance.last_verified",
                line,
            )
            if last_verified and last_verified > date.today():
                errors.append(f"[line {line}] last_verified is in the future")
        except ValueError as exc:
            errors.append(str(exc))

        for field in ["formats", "annotation_layers", "domain", "modality", "tags"]:
            values = item.get(field) or []
            if not isinstance(values, list):
                continue
            dupes = duplicates(values)
            if dupes:
                warnings.append(f"[line {line}] duplicate values in {field}: {', '.join(dupes)}")

        if not item.get("license"):
            warnings.append(f"[line {line}] missing license")

    if web_path and web_path.exists():
        try:
            web_items = json.loads(web_path.read_text(encoding="utf-8"))
            jsonl_items = [item for _, item in entries]
            if web_items != jsonl_items:
                errors.append("web/registry.json does not match data/registry.jsonl")
        except json.JSONDecodeError as exc:
            errors.append(f"web registry JSON parse error: {exc}")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("OK: quality checks passed.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in {2, 3}:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    registry = Path(sys.argv[1])
    web = Path(sys.argv[2]) if len(sys.argv) == 3 else None
    sys.exit(main(registry, web))
