#!/usr/bin/env python3
"""Validate built-in portrait recipe declarations without third-party packages."""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = {"schema_version", "id", "version", "title", "purpose", "privacy", "dimensions", "output"}

def validate(path: Path) -> list[str]:
    try:
        item = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{path.name}: invalid JSON ({error})"]
    errors: list[str] = []
    if not isinstance(item, dict): return [f"{path.name}: recipe must be an object"]
    if missing := REQUIRED - item.keys(): errors.append(f"{path.name}: missing {', '.join(sorted(missing))}")
    if item.get("schema_version") != "portrait-recipe/1.0": errors.append(f"{path.name}: bad schema_version")
    if not isinstance(item.get("id"), str) or not re.fullmatch(r"[a-z0-9-]+", item["id"]): errors.append(f"{path.name}: id must be kebab-case")
    if item.get("privacy") not in {"private_default", "public_candidate_after_calibration"}: errors.append(f"{path.name}: invalid privacy")
    dimensions = item.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions: errors.append(f"{path.name}: dimensions must be non-empty")
    else:
        for number, dimension in enumerate(dimensions, 1):
            minimum = dimension.get("minimum_evidence") if isinstance(dimension, dict) else None
            if not isinstance(dimension, dict) or not isinstance(dimension.get("question"), str) or not isinstance(minimum, dict) or minimum.get("seek_counterevidence") is not True or not isinstance(minimum.get("independent_contexts"), int) or minimum["independent_contexts"] < 1 or not isinstance(minimum.get("timespan_days"), int) or minimum["timespan_days"] < 0:
                errors.append(f"{path.name}: invalid evidence minimum for dimension {number}")
    output = item.get("output")
    if not isinstance(output, dict) or not isinstance(output.get("private_sections"), list) or not isinstance(output.get("public_forms"), list): errors.append(f"{path.name}: invalid output")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=Path(__file__).resolve().parents[1] / "recipes")
    selected = parser.parse_args().path
    paths = sorted(selected.glob("*.json")) if selected.is_dir() else [selected]
    errors = [error for path in paths for error in validate(path)] if paths else ["No recipe files found."]
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print(f"Validated {len(paths)} recipe file(s)."); return 0

if __name__ == "__main__": raise SystemExit(main())
