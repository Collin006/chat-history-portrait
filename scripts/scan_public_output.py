#!/usr/bin/env python3
"""Scan public portrait files for common privacy leaks.

This is a candidate detector, not proof of safety. Findings are written without
copying the matched private value into the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEXT_SUFFIXES = {".json", ".md", ".txt", ".csv"}
IGNORED_NAME = "privacy-scan.json"
PATTERNS = {
    "email": re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I),
    "url": re.compile(r"\bhttps?://[^\s<>()\]]+", re.I),
    "social_handle": re.compile(r"(?<![\w@])@[A-Za-z0-9_][A-Za-z0-9_.-]{1,31}\b"),
    "ipv4": re.compile(r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)"),
    "precise_date": re.compile(r"(?<!\d)(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])(?!\d)"),
    "cn_id_like": re.compile(r"(?<!\d)\d{17}[0-9Xx](?!\d)"),
    "phone_or_long_number": re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)"),
    "private_source_ref": re.compile(r"\bc\d{6}:u\d{4}\b"),
}
FORBIDDEN_KEYS = {
    "source_ref",
    "source_refs",
    "evidence",
    "excerpt",
    "quote",
    "conversation_id",
    "conversation_ref",
    "conversation_title",
    "raw_text",
}
MACHINE_DATE_KEYS = {"generated_at", "approved_at"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Public file or directory to scan")
    parser.add_argument("--report", type=Path, help="Report path (default: PATH/privacy-scan.json for a directory)")
    parser.add_argument("--fail-on-findings", action="store_true", help="Exit with status 3 when candidates are found")
    return parser.parse_args()


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def scan_json_content(value: Any, file: str, path: str = "$", key_name: str | None = None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.lower() in FORBIDDEN_KEYS:
                findings.append({"file": file, "kind": "forbidden_key", "location": child_path, "fingerprint": fingerprint(key)})
            findings.extend(scan_json_content(child, file, child_path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(scan_json_content(child, file, f"{path}[{index}]", key_name))
    elif isinstance(value, str):
        for kind, pattern in PATTERNS.items():
            if key_name in MACHINE_DATE_KEYS and kind in {"precise_date", "phone_or_long_number"}:
                continue
            for match in pattern.finditer(value):
                findings.append(
                    {
                        "file": file,
                        "kind": kind,
                        "location": path,
                        "start": match.start() + 1,
                        "fingerprint": fingerprint(match.group(0)),
                    }
                )
    return findings


def scan_file(path: Path, root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    relative = str(path.relative_to(root)) if path != root else path.name
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return findings, [f"{relative}: {error}"]
    if path.suffix.lower() == ".json":
        try:
            findings.extend(scan_json_content(json.loads(text), relative))
        except json.JSONDecodeError as error:
            errors.append(f"{relative}: invalid JSON: {error}")
    else:
        for line_number, line in enumerate(text.splitlines(), 1):
            for kind, pattern in PATTERNS.items():
                for match in pattern.finditer(line):
                    findings.append(
                        {
                            "file": relative,
                            "kind": kind,
                            "line": line_number,
                            "start": match.start() + 1,
                            "fingerprint": fingerprint(match.group(0)),
                        }
                    )
    return findings, errors


def main() -> int:
    args = parse_args()
    target = args.path.expanduser().resolve()
    if not target.exists():
        print(f"Scan target does not exist: {target}", file=sys.stderr)
        return 2
    root = target if target.is_dir() else target.parent
    paths = (
        sorted(path for path in target.rglob("*") if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and path.name != IGNORED_NAME)
        if target.is_dir()
        else [target]
    )
    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in paths:
        file_findings, file_errors = scan_file(path, root)
        findings.extend(file_findings)
        errors.extend(file_errors)
    report_path = args.report.expanduser().resolve() if args.report else root / IGNORED_NAME
    report = {
        "schema_version": "portrait-privacy-scan/1.0",
        "scanned_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "files_scanned": len(paths),
        "status": "review_required" if findings or errors else "no_automated_findings",
        "findings": findings,
        "scan_errors": errors,
        "limitations": [
            "Automated scanning cannot reliably identify names, places, organizations, rare anecdotes, or sensitive meaning.",
            "No automated finding is not proof that the package is safe to publish.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scanned {len(paths)} files; found {len(findings)} candidates. Report: {report_path}")
    if errors:
        return 2
    if findings and args.fail_on_findings:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
