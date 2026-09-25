#!/usr/bin/env python3
"""Validate private and public portrait artifacts without external packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
PRIVATE_SCHEMA = SKILL_DIR / "references" / "private-profile.schema.json"
PUBLIC_SCHEMA = SKILL_DIR / "references" / "public-profile.schema.json"
SOURCE_REF = re.compile(r"^c\d{6}:u\d{4}$")
FORBIDDEN_PUBLIC_KEYS = {
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path, help="Prepared portrait workspace")
    parser.add_argument("--stage", choices=("auto", "private", "public", "all"), default="auto")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local JSON Schema references are supported: {ref}")
    value: Any = schema
    for component in ref[2:].split("/"):
        value = value[component.replace("~1", "/").replace("~0", "~")]
    if not isinstance(value, dict):
        raise ValueError(f"Schema reference does not resolve to an object: {ref}")
    return value


def type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def validate_schema(instance: Any, node: dict[str, Any], root: dict[str, Any], path: str, errors: list[str]) -> None:
    if "$ref" in node:
        validate_schema(instance, resolve_ref(root, node["$ref"]), root, path, errors)
        return
    expected = node.get("type")
    if expected is not None:
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(type_matches(instance, item) for item in allowed):
            errors.append(f"{path}: expected type {allowed}, got {type(instance).__name__}")
            return
    if "const" in node and instance != node["const"]:
        errors.append(f"{path}: expected constant {node['const']!r}")
    if "enum" in node and instance not in node["enum"]:
        errors.append(f"{path}: expected one of {node['enum']!r}")
    if isinstance(instance, str):
        if len(instance) < node.get("minLength", 0):
            errors.append(f"{path}: string is shorter than minLength")
        if "pattern" in node and not re.search(node["pattern"], instance):
            errors.append(f"{path}: does not match required pattern")
        if node.get("format") == "date-time":
            try:
                datetime.fromisoformat(instance.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: invalid date-time")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in node and instance < node["minimum"]:
            errors.append(f"{path}: below minimum {node['minimum']}")
        if "maximum" in node and instance > node["maximum"]:
            errors.append(f"{path}: above maximum {node['maximum']}")
    if isinstance(instance, list):
        if len(instance) < node.get("minItems", 0):
            errors.append(f"{path}: fewer items than minItems")
        if isinstance(node.get("items"), dict):
            for index, item in enumerate(instance):
                validate_schema(item, node["items"], root, f"{path}[{index}]", errors)
    if isinstance(instance, dict):
        for required in node.get("required", []):
            if required not in instance:
                errors.append(f"{path}: missing required key {required!r}")
        properties = node.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                validate_schema(value, properties[key], root, f"{path}.{key}", errors)
            elif node.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected key {key!r}")


def collect_user_refs(corpus_path: Path, errors: list[str]) -> set[str]:
    references: set[str] = set()
    if not corpus_path.exists():
        errors.append(f"missing corpus: {corpus_path}")
        return references
    with corpus_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"{corpus_path}:{line_number}: invalid JSON: {error}")
                continue
            for turn in record.get("turns", []):
                if turn.get("role") == "user" and isinstance(turn.get("source_ref"), str):
                    references.add(turn["source_ref"])
    return references


def validate_checkpoint_coverage(workspace: Path, errors: list[str]) -> None:
    batch_dir = workspace / "private" / "batches"
    checkpoint_dir = workspace / "private" / "checkpoints"
    batches = sorted(batch_dir.glob("batch-*.jsonl"))
    if not batches:
        errors.append("no analysis batches found")
        return
    for batch in batches:
        checkpoint = checkpoint_dir / f"{batch.stem}.analysis.json"
        if not checkpoint.exists():
            errors.append(f"missing checkpoint for {batch.name}")
            continue
        try:
            payload = load_json(checkpoint)
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid checkpoint {checkpoint.name}: {error}")
            continue
        if payload.get("schema_version") != "portrait-checkpoint/1.0":
            errors.append(f"{checkpoint.name}: unsupported schema_version")
        if payload.get("batch_id") != batch.stem:
            errors.append(f"{checkpoint.name}: batch_id does not match filename")


def validate_private(workspace: Path, errors: list[str]) -> None:
    profile_path = workspace / "private" / "profile.json"
    if not profile_path.exists():
        errors.append(f"missing private profile: {profile_path}")
        return
    try:
        profile = load_json(profile_path)
        schema = load_json(PRIVATE_SCHEMA)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"cannot load private profile or schema: {error}")
        return
    validate_schema(profile, schema, schema, "$private", errors)
    user_refs = collect_user_refs(workspace / "private" / "corpus.jsonl", errors)
    claim_ids: set[str] = set()
    for index, claim in enumerate(profile.get("claims", [])):
        claim_id = claim.get("claim_id")
        if claim_id in claim_ids:
            errors.append(f"$private.claims[{index}]: duplicate claim_id {claim_id!r}")
        if isinstance(claim_id, str):
            claim_ids.add(claim_id)
        support_refs = []
        for evidence in claim.get("support", []) + claim.get("counterevidence", []):
            ref = evidence.get("source_ref") if isinstance(evidence, dict) else None
            if isinstance(ref, str):
                if not SOURCE_REF.fullmatch(ref):
                    errors.append(f"claim {claim_id}: malformed source_ref {ref!r}")
                elif ref not in user_refs:
                    errors.append(f"claim {claim_id}: source_ref {ref!r} not found in corpus")
                support_refs.append(ref)
        if claim.get("claim_type") == "observed_pattern":
            contexts = {ref.split(":", 1)[0] for ref in support_refs}
            if len(contexts) < 2:
                errors.append(f"claim {claim_id}: observed_pattern needs support from at least two conversations")
    validate_checkpoint_coverage(workspace, errors)


def walk_keys(value: Any, path: str = "$public") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.lower() in FORBIDDEN_PUBLIC_KEYS:
                found.append((child_path, key))
            found.extend(walk_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(walk_keys(child, f"{path}[{index}]"))
    return found


def validate_public(workspace: Path, errors: list[str]) -> None:
    profile_path = workspace / "public" / "profile.json"
    site_path = workspace / "public" / "site-package.json"
    calibration_path = workspace / "private" / "calibration.json"
    if not profile_path.exists():
        errors.append(f"missing public profile: {profile_path}")
        return
    if not site_path.exists():
        errors.append(f"missing website package: {site_path}")
        return
    if not calibration_path.exists():
        errors.append(f"missing calibration and consent record: {calibration_path}")
        return
    try:
        profile = load_json(profile_path)
        site_package = load_json(site_path)
        calibration = load_json(calibration_path)
        schema = load_json(PUBLIC_SCHEMA)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"cannot load public artifacts or schema: {error}")
        return
    validate_schema(profile, schema, schema, "$public.profile", errors)
    validate_schema(site_package, schema, schema, "$public.site-package", errors)
    if profile != site_package:
        errors.append("public/profile.json and public/site-package.json must be identical")
    if profile.get("identity_mode") == "anonymous" and profile.get("display", {}).get("name") is not None:
        errors.append("anonymous public profile must set display.name to null")
    if calibration.get("schema_version") != "portrait-calibration/1.0":
        errors.append("calibration record has unsupported schema_version")
    if calibration.get("public_consent") is not True:
        errors.append("calibration record does not grant public consent")
    if calibration.get("audience") != profile.get("audience"):
        errors.append("public profile audience does not match calibration record")
    if calibration.get("identity_mode") != profile.get("identity_mode"):
        errors.append("public profile identity_mode does not match calibration record")
    allowed_decisions = {"accept", "edit", "reject", "keep_private"}
    for index, decision in enumerate(calibration.get("decisions", [])):
        if not isinstance(decision, dict) or decision.get("decision") not in allowed_decisions:
            errors.append(f"calibration decision {index} is invalid")
    for key_path, key in walk_keys(profile):
        errors.append(f"{key_path}: forbidden public key {key!r}")
    serialized = json.dumps(profile, ensure_ascii=False)
    if re.search(r"c\d{6}:u\d{4}", serialized):
        errors.append("public profile contains a private source reference")


def main() -> int:
    args = parse_args()
    workspace = args.workspace.expanduser().resolve()
    errors: list[str] = []
    if not (workspace / "manifest.json").exists():
        errors.append(f"not a prepared workspace: {workspace}")
    stage = args.stage
    if stage == "auto":
        has_private = (workspace / "private" / "profile.json").exists()
        has_public = (workspace / "public" / "profile.json").exists() or (workspace / "public" / "site-package.json").exists()
        if not has_private and not has_public:
            errors.append("no private or public profile found to validate")
        if has_private:
            validate_private(workspace, errors)
        if has_public:
            validate_public(workspace, errors)
    else:
        if stage in {"private", "all"}:
            validate_private(workspace, errors)
        if stage in {"public", "all"}:
            validate_public(workspace, errors)
    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Validation passed for {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
