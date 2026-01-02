#!/usr/bin/env python3
"""
Check registry links for basic HTTP reachability.

Usage:
  python scripts/link_check.py data/registry.jsonl [--limit N] [--timeout SECONDS]
"""
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT = 10
USER_AGENT = "glottocode-registry-link-checker/0.1"


def load_jsonl(path: Path):
    items = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            items.append((i, json.loads(line)))
        except json.JSONDecodeError as exc:
            raise ValueError(f"[line {i}] JSON decode error: {exc}")
    return items


def request_status(url: str, timeout: int, method: str):
    headers = {"User-Agent": USER_AGENT}
    if method == "GET":
        headers["Range"] = "bytes=0-1024"
    req = Request(url, method=method, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        return resp.status


def check_url(url: str, timeout: int):
    try:
        return request_status(url, timeout, "HEAD"), None
    except HTTPError as exc:
        if exc.code in {405, 400, 403}:
            try:
                return request_status(url, timeout, "GET"), None
            except Exception as exc2:
                return None, str(exc2)
        return exc.code, None
    except URLError as exc:
        return None, str(exc)
    except Exception as exc:
        return None, str(exc)


def main(path: Path, limit: int | None, timeout: int) -> int:
    try:
        entries = load_jsonl(path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    checks = []
    for line, item in entries:
        for link in item.get("links", []):
            if not isinstance(link, dict):
                continue
            url = link.get("url")
            if url:
                checks.append((line, item.get("resource_id", "<missing>"), link.get("kind", "other"), url))

    if limit:
        checks = checks[:limit]

    warnings = []
    errors = []
    for line, resource_id, kind, url in checks:
        status, err = check_url(url, timeout)
        if err:
            errors.append(f"[line {line}] {resource_id} ({kind}) {url} -> {err}")
            continue
        if status is None:
            errors.append(f"[line {line}] {resource_id} ({kind}) {url} -> unknown error")
            continue
        if 200 <= status < 400:
            continue
        if status in {401, 403, 429}:
            warnings.append(f"[line {line}] {resource_id} ({kind}) {url} -> HTTP {status}")
            continue
        errors.append(f"[line {line}] {resource_id} ({kind}) {url} -> HTTP {status}")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("OK: link checks passed.")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    limit = None
    timeout = DEFAULT_TIMEOUT
    if not args:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    path = Path(args[0])
    i = 1
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        elif args[i] == "--timeout" and i + 1 < len(args):
            timeout = int(args[i + 1])
            i += 2
        else:
            print("Unknown option. Use --limit or --timeout.", file=sys.stderr)
            sys.exit(2)
    sys.exit(main(path, limit, timeout))
