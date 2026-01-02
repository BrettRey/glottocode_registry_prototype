#!/usr/bin/env python3
"""
Generate Wikipedia dump registry entries from Wikimedia sitematrix.

Usage:
  python scripts/generate_wikipedia_entries.py data/registry.jsonl --count 100 --append
"""
import argparse
import csv
import io
import json
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

SITEMATRIX_URL = (
    "https://www.mediawiki.org/w/api.php?action=sitematrix&format=json"
    "&smlimit=5000&smsiteprop=code|dbname|lang|sitename|url|closed|fishbowl"
)
ISO639_3_URL = "https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3.tab"
GLOTTOLOG_URL = "https://cdstar.eva.mpg.de/bitstreams/EAEA0-2198-D710-AA36-0/glottolog_languoid.csv.zip"
USER_AGENT = "glottocode-registry/0.1 (registry prototype)"


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
        iso3 = (row.get("Id") or "").strip()
        iso1 = (row.get("Part1") or "").strip()
        if iso1 and iso3:
            iso1_to_3[iso1.lower()] = iso3.lower()
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


def extract_wikipedia_sites(sitematrix: dict) -> list[dict]:
    sites = []
    matrix = sitematrix.get("sitematrix", {})
    for key, value in matrix.items():
        if key in {"count", "specials"}:
            continue
        if not isinstance(value, dict):
            continue
        code = (value.get("code") or "").lower()
        if not code.isalpha() or len(code) not in {2, 3}:
            continue
        for site in value.get("site", []):
            if site.get("code") != "wiki":
                continue
            if site.get("closed") or site.get("fishbowl"):
                continue
            sites.append(
                {
                    "code": code,
                    "dbname": site.get("dbname"),
                    "url": site.get("url"),
                }
            )
    return sites


def build_entry(iso3: str, glottocode: str, name: str, dbname: str) -> dict:
    today = date.today().isoformat()
    title = f"Wikipedia dump for {name}"
    description = f"Wikipedia XML dump for {name} (open text corpus)."
    landing = f"https://dumps.wikimedia.org/{dbname}/"
    return {
        "resource_id": f"wikipedia-{iso3}",
        "glottocode": glottocode,
        "title": title,
        "description": description,
        "resource_type": "corpus",
        "modality": ["text"],
        "domain": ["other"],
        "formats": ["xml"],
        "license": "CC-BY-SA-4.0",
        "access": {"level": "open", "constraints": []},
        "links": [{"kind": "landing", "url": landing}],
        "provenance": {
            "source_catalog": "wikimedia",
            "source_record": dbname,
            "last_verified": today,
        },
        "created": today,
        "curation": {"status": "seed", "maintainers": ["@you"], "notes": "Generated from Wikimedia dumps."},
        "tags": ["wikipedia", "dump"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Wikipedia dump entries.")
    parser.add_argument("output", help="JSONL output file")
    parser.add_argument("--count", type=int, default=100, help="Number of entries to generate")
    parser.add_argument("--append", action="store_true", help="Append to output JSONL")
    args = parser.parse_args()

    output_path = Path(args.output)
    existing_ids = load_existing_ids(output_path) if args.append else set()

    iso1_to_3 = load_iso_mappings()
    iso3_to_glotto = load_glottolog_mappings()
    sitematrix = fetch_json(SITEMATRIX_URL)
    sites = extract_wikipedia_sites(sitematrix)

    entries = []
    used_ids = set(existing_ids)

    for site in sites:
        code = site["code"]
        iso3 = iso1_to_3.get(code, code)
        glotto = iso3_to_glotto.get(iso3)
        if not glotto:
            continue
        rid = f"wikipedia-{iso3}"
        if rid in used_ids:
            continue
        entry = build_entry(iso3, glotto["glottocode"], glotto["name"], site["dbname"])
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
