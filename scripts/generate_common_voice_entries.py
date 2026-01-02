#!/usr/bin/env python3
"""
Generate Mozilla Common Voice entries (non-Wikimedia).

Usage:
  python scripts/generate_common_voice_entries.py data/registry.jsonl --count 100 --append
"""
import argparse
import csv
import io
import json
import re
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

ISO639_3_URL = "https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab"
GLOTTOLOG_URL = "https://cdstar.eva.mpg.de/bitstreams/EAEA0-2198-D710-AA36-0/glottolog_languoid.csv.zip"
GITHUB_API_DATASETS = "https://api.github.com/repos/common-voice/cv-dataset/contents/datasets"
RAW_DATASET_URL = "https://raw.githubusercontent.com/common-voice/cv-dataset/main/datasets/{name}"
USER_AGENT = "glottocode-registry/0.1 (registry prototype)"
DATASET_LANDING = "https://commonvoice.mozilla.org/en/datasets"


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def load_iso_mappings() -> dict:
    text = fetch_text(ISO639_3_URL)
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    iso1_to_3 = {}
    for row in reader:
        iso3 = (row.get("Id") or "").strip().lower()
        iso1 = (row.get("Part1") or "").strip().lower()
        if iso1 and iso3:
            iso1_to_3[iso1] = iso3
    return iso1_to_3


def load_glottolog_mappings() -> dict:
    req = urllib.request.Request(GLOTTOLOG_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        with zf.open("languoid.csv") as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8"))
            mapping = {}
            for row in reader:
                iso = (row.get("iso639P3code") or "").strip().lower()
                level = (row.get("level") or "").strip().lower()
                if not iso or level != "language":
                    continue
                if iso not in mapping:
                    mapping[iso] = {
                        "glottocode": row.get("id"),
                        "name": row.get("name"),
                    }
            return mapping


def load_existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = obj.get("resource_id")
        if rid:
            ids.add(rid)
    return ids


def find_latest_dataset_name() -> str:
    data = fetch_json(GITHUB_API_DATASETS)
    pattern = re.compile(r"cv-corpus-(\d+\.\d+)-(\d{4}-\d{2}-\d{2})\.json")
    entries = []
    for item in data:
        if item.get("type") != "file":
            continue
        name = item.get("name", "")
        match = pattern.match(name)
        if not match:
            continue
        date_str = match.group(2)
        version = match.group(1)
        entries.append((date_str, version, name))
    if not entries:
        raise RuntimeError("No cv-corpus dataset files found")
    entries.sort()
    return entries[-1][2]


def load_dataset_locales() -> dict:
    name = find_latest_dataset_name()
    raw_url = RAW_DATASET_URL.format(name=name)
    data = fetch_json(raw_url)
    locales = data.get("locales", {})
    if not isinstance(locales, dict):
        raise RuntimeError("Unexpected locales structure")
    return locales


def normalize_locale(locale: str) -> str:
    return locale.replace("_", "-").strip()


def locale_to_iso3(locale: str, iso1_to_3: dict) -> str | None:
    base = locale.split("-")[0].lower()
    if len(base) == 2:
        return iso1_to_3.get(base)
    if len(base) == 3:
        return base
    return None


def build_entry(locale: str, iso3: str, glottocode: str, name: str) -> dict:
    today = date.today().isoformat()
    normalized_locale = normalize_locale(locale)
    title = f"Mozilla Common Voice {name}"
    description = f"Open speech corpus from Mozilla Common Voice for {name}."
    return {
        "resource_id": f"common-voice-{normalized_locale.lower()}",
        "glottocode": glottocode,
        "title": title,
        "description": description,
        "resource_type": "corpus",
        "modality": ["audio", "text"],
        "domain": ["phonetics"],
        "formats": ["mp3", "tsv"],
        "annotation_layers": ["orthographic transcription"],
        "license": "CC0-1.0",
        "access": {"level": "open", "constraints": []},
        "links": [{"kind": "landing", "url": DATASET_LANDING}],
        "provenance": {
            "source_catalog": "mozilla-common-voice",
            "source_record": normalized_locale,
            "last_verified": today,
        },
        "created": today,
        "curation": {
            "status": "seed",
            "maintainers": ["@you"],
            "notes": "Generated from Common Voice dataset metadata.",
        },
        "tags": ["common-voice", "speech"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Common Voice entries.")
    parser.add_argument("output", help="JSONL output file")
    parser.add_argument("--count", type=int, default=100, help="Number of entries to generate")
    parser.add_argument("--append", action="store_true", help="Append to output JSONL")
    args = parser.parse_args()

    output_path = Path(args.output)
    existing_ids = load_existing_ids(output_path) if args.append else set()

    iso1_to_3 = load_iso_mappings()
    iso3_to_glotto = load_glottolog_mappings()
    locales = load_dataset_locales()

    def locale_score(item):
        locale, stats = item
        valid_hrs = stats.get("validHrs")
        if valid_hrs is None:
            valid_secs = stats.get("validDurationSecs") or 0
            return float(valid_secs)
        return float(valid_hrs)

    sorted_locales = sorted(locales.items(), key=locale_score, reverse=True)

    entries = []
    used_ids = set(existing_ids)

    for locale, _stats in sorted_locales:
        normalized = normalize_locale(locale)
        rid = f"common-voice-{normalized.lower()}"
        if rid in used_ids:
            continue
        iso3 = locale_to_iso3(locale, iso1_to_3)
        if not iso3:
            continue
        glotto = iso3_to_glotto.get(iso3)
        if not glotto:
            continue
        entry = build_entry(locale, iso3, glotto["glottocode"], glotto["name"])
        entries.append(entry)
        used_ids.add(rid)
        if len(entries) >= args.count:
            break

    if len(entries) < args.count:
        print(f"Warning: only generated {len(entries)} entries", file=sys.stderr)

    output_lines = "\n".join(json.dumps(entry, ensure_ascii=True) for entry in entries) + "\n"
    if args.append and output_path.exists():
        with output_path.open("a", encoding="utf-8") as fh:
            fh.write(output_lines)
    else:
        output_path.write_text(output_lines, encoding="utf-8")

    print(f"Wrote {len(entries)} entries to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
