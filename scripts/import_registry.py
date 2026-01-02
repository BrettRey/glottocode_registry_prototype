#!/usr/bin/env python3
"""
Import registry entries from CSV/TSV into JSONL.

Usage:
  python scripts/import_registry.py input.csv output.jsonl
  python scripts/import_registry.py input.tsv output.jsonl --append

Defaults:
- access.level defaults to "open"
- created defaults to today (ISO date)
- curation.status defaults to "seed"
- curation.maintainers defaults to "@you"
"""
import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path


CANONICAL_FIELDS = {
    "resource_id",
    "glottocode",
    "glottocodes_secondary",
    "title",
    "description",
    "resource_type",
    "modality",
    "domain",
    "formats",
    "annotation_layers",
    "license",
    "access_level",
    "access_constraints",
    "access_contact",
    "landing_url",
    "links",
    "link_download",
    "link_api",
    "link_code",
    "link_doi",
    "link_paper",
    "link_other",
    "citation_preferred",
    "citation_bibtex",
    "provenance_source_catalog",
    "provenance_source_record",
    "provenance_last_verified",
    "created",
    "updated",
    "curation_status",
    "curation_maintainers",
    "curation_notes",
    "tags",
}

ALIASES = {
    "resourceid": "resource_id",
    "resource": "resource_id",
    "glottocodes": "glottocode",
    "secondary_glottocodes": "glottocodes_secondary",
    "secondary_glottocode": "glottocodes_secondary",
    "glottocode_secondary": "glottocodes_secondary",
    "format": "formats",
    "annotation_layer": "annotation_layers",
    "access": "access_level",
    "landing": "landing_url",
    "landing_page": "landing_url",
    "landingpage": "landing_url",
    "download_url": "link_download",
    "api_url": "link_api",
    "code_url": "link_code",
    "doi": "link_doi",
    "paper_url": "link_paper",
    "other_url": "link_other",
    "curation_status": "curation_status",
    "status": "curation_status",
    "maintainers": "curation_maintainers",
    "curation_maintainers": "curation_maintainers",
    "curation_notes": "curation_notes",
    "source_catalog": "provenance_source_catalog",
    "source_record": "provenance_source_record",
    "last_verified": "provenance_last_verified",
    "citation": "citation_preferred",
}

REQUIRED_FIELDS = {"resource_id", "glottocode", "title", "resource_type", "license", "landing_url"}

LIST_FIELDS = {
    "glottocodes_secondary",
    "modality",
    "domain",
    "formats",
    "annotation_layers",
    "tags",
    "access_constraints",
    "curation_maintainers",
}

LINK_FIELDS = {
    "link_download": "download",
    "link_api": "api",
    "link_code": "code",
    "link_doi": "doi",
    "link_paper": "paper",
    "link_other": "other",
}


def normalize_header(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    cleaned = cleaned.strip("_")
    return cleaned


def parse_list(value: str) -> list[str]:
    if value is None:
        return []
    value = value.strip()
    if not value:
        return []
    parts = re.split(r"[;,|]", value)
    return [part.strip() for part in parts if part.strip()]


def parse_date(value: str, field: str, row_num: int) -> str:
    value = value.strip()
    if not value:
        return ""
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"[row {row_num}] invalid date for {field}: {value}")
    return value


def parse_links(row: dict, row_num: int, errors: list[str], warnings: list[str]) -> list[dict]:
    links = []

    def add_link(kind: str, url: str):
        url = url.strip()
        if not url:
            return
        links.append({"kind": kind, "url": url})

    landing = row.get("landing_url", "").strip()
    if not landing:
        errors.append(f"[row {row_num}] missing landing_url")
    else:
        add_link("landing", landing)

    for field, kind in LINK_FIELDS.items():
        url = row.get(field, "")
        if url:
            add_link(kind, url)

    raw_links = row.get("links", "")
    if raw_links:
        for chunk in re.split(r"[|;]", raw_links):
            chunk = chunk.strip()
            if not chunk:
                continue
            if ":" not in chunk:
                warnings.append(f"[row {row_num}] invalid links entry: {chunk}")
                continue
            kind, url = chunk.split(":", 1)
            kind = kind.strip()
            url = url.strip()
            if not kind or not url:
                warnings.append(f"[row {row_num}] invalid links entry: {chunk}")
                continue
            add_link(kind, url)

    deduped = []
    seen = set()
    for link in links:
        key = (link.get("kind"), link.get("url"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(link)
    return deduped


def build_entry(row: dict, row_num: int, defaults: dict, errors: list[str], warnings: list[str]) -> dict | None:
    entry = {}

    for field in REQUIRED_FIELDS:
        if not row.get(field, "").strip():
            errors.append(f"[row {row_num}] missing required field: {field}")

    if errors:
        return None

    entry["resource_id"] = row["resource_id"].strip()
    entry["glottocode"] = row["glottocode"].strip()

    secondary = parse_list(row.get("glottocodes_secondary", ""))
    if secondary:
        entry["glottocodes_secondary"] = secondary

    entry["title"] = row["title"].strip()

    description = row.get("description", "").strip()
    if description:
        entry["description"] = description

    entry["resource_type"] = row["resource_type"].strip()

    for field in ["modality", "domain", "formats", "annotation_layers"]:
        values = parse_list(row.get(field, ""))
        if values:
            entry[field] = values

    license_value = row.get("license", "").strip()
    if license_value:
        entry["license"] = license_value

    access_level = row.get("access_level", "").strip() or defaults["access_level"]
    if access_level and access_level != "open" and not defaults["allow_non_open"]:
        errors.append(f"[row {row_num}] access_level must be open (got {access_level})")
    access = {"level": access_level or "open"}
    constraints = parse_list(row.get("access_constraints", ""))
    if constraints:
        access["constraints"] = constraints
    contact = row.get("access_contact", "").strip()
    if contact:
        access["contact"] = contact
    entry["access"] = access

    links = parse_links(row, row_num, errors, warnings)
    if links:
        entry["links"] = links

    citation_preferred = row.get("citation_preferred", "").strip()
    citation_bibtex = row.get("citation_bibtex", "").strip()
    if citation_preferred or citation_bibtex:
        citation = {}
        if citation_preferred:
            citation["preferred"] = citation_preferred
        if citation_bibtex:
            citation["bibtex"] = citation_bibtex
        entry["citation"] = citation

    provenance_source_catalog = row.get("provenance_source_catalog", "").strip()
    provenance_source_record = row.get("provenance_source_record", "").strip()
    provenance_last_verified = row.get("provenance_last_verified", "").strip()
    if provenance_source_catalog or provenance_source_record or provenance_last_verified:
        provenance = {}
        if provenance_source_catalog:
            provenance["source_catalog"] = provenance_source_catalog
        if provenance_source_record:
            provenance["source_record"] = provenance_source_record
        if provenance_last_verified:
            try:
                provenance["last_verified"] = parse_date(
                    provenance_last_verified, "provenance.last_verified", row_num
                )
            except ValueError as exc:
                errors.append(str(exc))
        entry["provenance"] = provenance

    created_value = row.get("created", "").strip() or defaults["created"]
    try:
        entry["created"] = parse_date(created_value, "created", row_num)
    except ValueError as exc:
        errors.append(str(exc))

    updated_value = row.get("updated", "").strip()
    if updated_value:
        try:
            entry["updated"] = parse_date(updated_value, "updated", row_num)
        except ValueError as exc:
            errors.append(str(exc))

    curation_status = row.get("curation_status", "").strip() or defaults["curation_status"]
    curation_maintainers = parse_list(row.get("curation_maintainers", "")) or defaults["curation_maintainers"]
    curation_notes = row.get("curation_notes", "").strip()
    entry["curation"] = {
        "status": curation_status,
        "maintainers": curation_maintainers,
    }
    if curation_notes:
        entry["curation"]["notes"] = curation_notes

    tags = parse_list(row.get("tags", ""))
    if tags:
        entry["tags"] = tags

    if errors:
        return None
    return entry


def determine_delimiter(path: Path, explicit: str | None) -> str:
    if explicit and explicit != "auto":
        return "\t" if explicit == "\\t" else explicit
    if path.suffix.lower() == ".tsv":
        return "\t"
    if path.suffix.lower() == ".csv":
        return ","
    sample = path.read_text(encoding="utf-8")[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample)
        return dialect.delimiter
    except csv.Error:
        return ","


def main() -> int:
    parser = argparse.ArgumentParser(description="Import registry entries from CSV/TSV.")
    parser.add_argument("input", help="CSV/TSV input file")
    parser.add_argument("output", help="Output JSONL file (or use - for stdout)")
    parser.add_argument("--append", action="store_true", help="Append to output file")
    parser.add_argument("--delimiter", default="auto", help="Delimiter: auto, ',', or '\\t'")
    parser.add_argument("--default-maintainers", default="@you", help="Default curation maintainers (comma-separated)")
    parser.add_argument("--default-curation-status", default="seed", help="Default curation status")
    parser.add_argument("--default-created", default=date.today().isoformat(), help="Default created date (YYYY-MM-DD)")
    parser.add_argument("--allow-non-open", action="store_true", help="Allow non-open access levels")

    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    delimiter = determine_delimiter(input_path, args.delimiter)
    defaults = {
        "created": args.default_created,
        "curation_status": args.default_curation_status,
        "curation_maintainers": parse_list(args.default_maintainers) or ["@you"],
        "access_level": "open",
        "allow_non_open": args.allow_non_open,
    }

    text = input_path.read_text(encoding="utf-8")
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    if not reader.fieldnames:
        print("Missing header row", file=sys.stderr)
        return 1

    normalized_headers = {}
    unknown_headers = []
    for header in reader.fieldnames:
        norm = normalize_header(header)
        canonical = ALIASES.get(norm, norm)
        if canonical in CANONICAL_FIELDS:
            normalized_headers[header] = canonical
        else:
            unknown_headers.append(header)

    if unknown_headers:
        print("Warning: unknown columns will be ignored:", ", ".join(unknown_headers), file=sys.stderr)

    errors = []
    warnings = []
    entries = []

    for row_num, row in enumerate(reader, start=2):
        normalized_row = {}
        for raw_key, value in row.items():
            canonical = normalized_headers.get(raw_key)
            if not canonical:
                continue
            value = value or ""
            if canonical in normalized_row and value.strip():
                warnings.append(f"[row {row_num}] duplicate column for {canonical}; keeping first")
                continue
            normalized_row[canonical] = value

        if not any(value.strip() for value in normalized_row.values()):
            continue

        entry = build_entry(normalized_row, row_num, defaults, errors, warnings)
        if entry:
            entries.append(entry)

    if warnings:
        print("Warnings:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)

    if errors:
        print("Errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    output_lines = "\n".join(json.dumps(entry, ensure_ascii=True) for entry in entries) + "\n"
    if args.output == "-":
        sys.stdout.write(output_lines)
        return 0

    if args.append and output_path.exists():
        with output_path.open("a", encoding="utf-8") as fh:
            fh.write(output_lines)
    else:
        output_path.write_text(output_lines, encoding="utf-8")
    print(f"Wrote {len(entries)} entries to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
