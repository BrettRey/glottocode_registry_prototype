#!/usr/bin/env python3
"""
Generate Language Science Press grammar entries (non-Wikimedia).

Usage:
  python scripts/generate_langsci_grammar_entries.py data/registry.jsonl --count 100 --append
"""
import argparse
import csv
import io
import json
import re
import sys
import unicodedata
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

CATALOG_URL = "https://langsci-press.org/catalogSearch"
BOOK_URL = "https://langsci-press.org/catalog/book/{book_id}"
GLOTTOLOG_URL = "https://cdstar.eva.mpg.de/bitstreams/EAEA0-2198-D710-AA36-0/glottolog_languoid.csv.zip"
ISO_NAME_INDEX_URL = "https://iso639-3.sil.org/sites/iso639-3/files/downloads/iso-639-3_Name_Index.tab"
USER_AGENT = "glottocode-registry/0.1 (registry prototype)"

TITLE_PATTERNS = [
    re.compile(r"\bgrammar of\b", re.IGNORECASE),
    re.compile(r"\bgrammar and dictionary of\b", re.IGNORECASE),
    re.compile(r"\bdictionary and grammatical sketch of\b", re.IGNORECASE),
    re.compile(r"\bgrammatical sketch of\b", re.IGNORECASE),
]

MANUAL_OVERRIDES = {
    "dagaare": "sout2789",
    "ruruuli lunyala": "ruul1235",
    "ruruuli-lunyala": "ruul1235",
    "ruruuli": "ruul1235",
    "choguita raramuri": "cent2131",
    "gyeli": "gyel1242",
    "gyele": "gyel1242",
    "rapa nui": "rapa1244",
    "sanzhi dargwa": "sanz1248",
    "sanzhi": "sanz1248",
    "tuatschin": "roma1326",
    "andaki": "anda1286",
    "andaki language": "anda1286",
    "andakí": "anda1286",
    "iranian armenian": "nucl1235",
    "parskahayeren": "nucl1235",
    "iranahayeren": "nucl1235",
}


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_anchor = False
        self.current_href = None
        self.current_text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = None
            for key, value in attrs:
                if key.lower() == "href":
                    href = value
                    break
            if href and "/catalog/book/" in href:
                self.in_anchor = True
                self.current_href = href
                self.current_text = []

    def handle_data(self, data):
        if self.in_anchor:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.in_anchor:
            text = "".join(self.current_text).strip()
            if text:
                self.links.append((self.current_href, text))
            self.in_anchor = False
            self.current_href = None
            self.current_text = []


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def fetch_binary(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    name = re.sub(r"[^a-z0-9]+", " ", name)
    return " ".join(name.split())


def load_glottolog_names() -> dict:
    import zipfile

    data = fetch_binary(GLOTTOLOG_URL)
    mapping = {}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        with zf.open("languoid.csv") as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8"))
            for row in reader:
                name = (row.get("name") or "").strip()
                glottocode = (row.get("id") or "").strip()
                if not name or not glottocode:
                    continue
                normalized = normalize_name(name)
                mapping.setdefault(normalized, set()).add(glottocode)
                if "(" in name and ")" in name:
                    base = re.sub(r"\s*\(.*?\)\s*", " ", name).strip()
                    base_norm = normalize_name(base)
                    if base_norm:
                        mapping.setdefault(base_norm, set()).add(glottocode)
    unique = {k: list(v)[0] for k, v in mapping.items() if len(v) == 1}
    return unique


def load_iso_name_index() -> dict:
    text = fetch_text(ISO_NAME_INDEX_URL)
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    mapping = {}
    for row in reader:
        iso = (row.get("Id") or "").strip().lower()
        for key in ["Print_Name", "Inverted_Name"]:
            name = (row.get(key) or "").strip()
            if not iso or not name:
                continue
            normalized = normalize_name(name)
            mapping.setdefault(normalized, set()).add(iso)
    return mapping


def load_iso_to_glottocode() -> dict:
    import zipfile

    data = fetch_binary(GLOTTOLOG_URL)
    mapping = {}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        with zf.open("languoid.csv") as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8"))
            for row in reader:
                iso = (row.get("iso639P3code") or "").strip().lower()
                glottocode = (row.get("id") or "").strip()
                level = (row.get("level") or "").strip().lower()
                if not iso or not glottocode or level != "language":
                    continue
                if iso not in mapping:
                    mapping[iso] = glottocode
    return mapping


def extract_language_from_title(title: str) -> str | None:
    if not title:
        return None
    title = re.sub(r"^\d+\s+", "", title).strip()
    for pattern in TITLE_PATTERNS:
        match = pattern.search(title)
        if match:
            start = match.end()
            language = title[start:].strip()
            language = re.split(r":\s+|\\s+–\\s+|\\s+-\\s+", language, maxsplit=1)[0].strip()
            return language
    if title.lower().startswith("a grammar of "):
        language = title[len("a grammar of "):].strip()
        language = re.split(r":\s+|\\s+–\\s+|\\s+-\\s+", language, maxsplit=1)[0].strip()
        return language
    if title.lower().startswith("grammar of "):
        language = title[len("grammar of "):].strip()
        language = re.split(r":\s+|\\s+–\\s+|\\s+-\\s+", language, maxsplit=1)[0].strip()
        return language
    return None


def is_grammar_title(title: str) -> bool:
    if not title:
        return False
    lowered = title.lower()
    if "forthcoming" in lowered or "superseded" in lowered:
        return False
    return any(pattern.search(title) for pattern in TITLE_PATTERNS) or lowered.startswith("a grammar of ")


def candidate_name_variants(language: str) -> list[str]:
    variants = []
    if language:
        variants.append(language)
        if "(" in language and ")" in language:
            inside = re.search(r"\((.*?)\)", language)
            if inside and inside.group(1).strip():
                variants.append(inside.group(1).strip())
            base = re.sub(r"\s*\(.*?\)\s*", " ", language).strip()
            if base and base not in variants:
                variants.append(base)
        if "/" in language or "-" in language:
            for part in re.split(r"[/|-]", language):
                part = part.strip()
                if part and part not in variants:
                    variants.append(part)
    return variants


def resolve_glottocode(language: str, name_map: dict, iso_name_map: dict, iso_to_glotto: dict) -> str | None:
    variants = candidate_name_variants(language)
    for variant in variants:
        norm = normalize_name(variant)
        override = MANUAL_OVERRIDES.get(norm)
        if override:
            return override
        glotto = name_map.get(norm)
        if glotto:
            return glotto

    for variant in variants:
        norm = normalize_name(variant)
        iso_candidates = iso_name_map.get(norm)
        if not iso_candidates:
            continue
        if len(iso_candidates) == 1:
            iso = next(iter(iso_candidates))
            glotto = iso_to_glotto.get(iso)
            if glotto:
                return glotto

    # Substring fallback (unique only)
    norm = normalize_name(language)
    if norm:
        matches = [code for name, code in name_map.items() if norm in name]
        unique = list({m for m in matches})
        if len(unique) == 1:
            return unique[0]
    return None


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


def parse_book_page(book_id: str) -> dict:
    html = fetch_text(BOOK_URL.format(book_id=book_id))
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
    if not title:
        title = ""
    if "Forthcoming" in title or "Superseded" in title:
        return {}
    license_ok = bool(re.search(r"Creative Commons Attribution", html, re.IGNORECASE) or re.search(r"CC\\s*BY", html, re.IGNORECASE))
    doi_match = re.search(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", html, re.IGNORECASE)
    doi = doi_match.group(1) if doi_match else ""
    cite_match = re.search(r"Cite as\s*(.*?)\s*(Copy BibTeX|Copyright)", html, re.IGNORECASE | re.DOTALL)
    citation = ""
    if cite_match:
        citation = re.sub(r"\s+", " ", cite_match.group(1)).strip()
    return {
        "title": title,
        "doi": doi,
        "citation": citation,
        "license_ok": license_ok,
    }


def build_entry(book_id: str, title: str, glottocode: str, doi: str, citation: str) -> dict:
    today = date.today().isoformat()
    landing = BOOK_URL.format(book_id=book_id)
    links = [{"kind": "landing", "url": landing}]
    if doi:
        links.append({"kind": "doi", "url": f"https://doi.org/{doi}"})
    entry = {
        "resource_id": f"langsci-grammar-{book_id}",
        "glottocode": glottocode,
        "title": title,
        "description": "Open-access reference grammar published by Language Science Press.",
        "resource_type": "grammar",
        "modality": ["text"],
        "domain": ["documentation"],
        "formats": ["pdf"],
        "license": "CC-BY-4.0",
        "access": {"level": "open", "constraints": []},
        "links": links,
        "citation": {"preferred": citation} if citation else None,
        "provenance": {
            "source_catalog": "langsci-press",
            "source_record": book_id,
            "last_verified": today,
        },
        "created": today,
        "curation": {
            "status": "seed",
            "maintainers": ["@you"],
            "notes": "Generated from Language Science Press catalog.",
        },
        "tags": ["grammar", "langsci"],
    }
    if entry.get("citation") is None:
        entry.pop("citation")
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Language Science Press grammar entries.")
    parser.add_argument("output", help="JSONL output file")
    parser.add_argument("--count", type=int, default=100, help="Number of entries to generate")
    parser.add_argument("--append", action="store_true", help="Append to output JSONL")
    args = parser.parse_args()

    output_path = Path(args.output)
    existing_ids = load_existing_ids(output_path) if args.append else set()

    catalog_html = fetch_text(CATALOG_URL)
    parser_html = AnchorParser()
    parser_html.feed(catalog_html)

    candidates = []
    for href, text in parser_html.links:
        match = re.search(r"/catalog/book/(\d+)", href)
        if not match:
            continue
        book_id = match.group(1)
        if not is_grammar_title(text):
            continue
        candidates.append((book_id, text))

    glottolog_map = load_glottolog_names()
    iso_name_map = load_iso_name_index()
    iso_to_glotto = load_iso_to_glottocode()

    entries = []
    used_ids = set(existing_ids)
    for book_id, text in candidates:
        rid = f"langsci-grammar-{book_id}"
        if rid in used_ids:
            continue
        book_info = parse_book_page(book_id)
        if not book_info:
            continue
        if not book_info.get("license_ok"):
            continue
        title = book_info.get("title") or text
        language = extract_language_from_title(title)
        if not language:
            continue
        glottocode = resolve_glottocode(language, glottolog_map, iso_name_map, iso_to_glotto)
        if not glottocode:
            continue
        entry = build_entry(book_id, title, glottocode, book_info.get("doi", ""), book_info.get("citation", ""))
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
