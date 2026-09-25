#!/usr/bin/env python3
"""Prepare a private, batched corpus from an official ChatGPT data export.

The script accepts an export ZIP, an extracted export directory, or a
conversations.json file. It makes no network calls and writes the output
workspace atomically.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import sys
import uuid
import zipfile
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Iterator

MANIFEST_VERSION = "chat-history-corpus/1.0"
RECORD_VERSION = "chat-history-record/1.0"
DEFAULT_BATCH_CHARS = 160_000
DEFAULT_MAX_JSON_MB = 2_048


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def iso_timestamp(value: Any) -> str | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (OverflowError, OSError, ValueError):
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Export ZIP, extracted directory, or conversations.json")
    parser.add_argument("--out", required=True, type=Path, help="Unused output directory")
    parser.add_argument(
        "--batch-chars",
        type=int,
        default=DEFAULT_BATCH_CHARS,
        help=f"Approximate maximum characters per analysis batch (default: {DEFAULT_BATCH_CHARS})",
    )
    parser.add_argument(
        "--max-json-mb",
        type=int,
        default=DEFAULT_MAX_JSON_MB,
        help=f"Reject conversations.json larger than this many MiB (default: {DEFAULT_MAX_JSON_MB})",
    )
    return parser.parse_args()


class ConversationSource:
    def __init__(self, path: Path, zip_member: str | None = None, size: int | None = None) -> None:
        self.path = path
        self.zip_member = zip_member
        self.size = size if size is not None else path.stat().st_size

    @property
    def label(self) -> str:
        return self.path.name

    @contextmanager
    def open_binary(self) -> Iterator[BinaryIO]:
        if self.zip_member is None:
            with self.path.open("rb") as handle:
                yield handle
            return
        with zipfile.ZipFile(self.path) as archive:
            with archive.open(self.zip_member, "r") as handle:
                yield handle


def locate_source(source: Path) -> ConversationSource:
    if source.is_file() and source.name == "conversations.json":
        return ConversationSource(source)
    if source.is_file() and zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            matches = [
                item
                for item in archive.infolist()
                if not item.is_dir() and Path(item.filename).name == "conversations.json"
            ]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one conversations.json in ZIP; found {len(matches)}")
        return ConversationSource(source, matches[0].filename, matches[0].file_size)
    if source.is_dir():
        matches = [path for path in source.rglob("conversations.json") if path.is_file()]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one conversations.json in directory; found {len(matches)}")
        return ConversationSource(matches[0])
    raise ValueError("Source must be an export ZIP, extracted directory, or conversations.json")


def load_json(source: ConversationSource, max_bytes: int) -> tuple[list[Any], str]:
    if source.size > max_bytes:
        raise ValueError(
            f"conversations.json is {source.size / 1_048_576:.1f} MiB, above the configured limit "
            f"of {max_bytes / 1_048_576:.1f} MiB"
        )
    digest = hashlib.sha256()
    with source.open_binary() as binary:
        while chunk := binary.read(1024 * 1024):
            digest.update(chunk)
    with source.open_binary() as binary:
        with io.TextIOWrapper(binary, encoding="utf-8-sig") as text:
            payload = json.load(text)
    if not isinstance(payload, list):
        raise ValueError("conversations.json must contain a top-level list")
    return payload, digest.hexdigest()


def render_part(part: Any) -> tuple[list[str], int]:
    if isinstance(part, str):
        return ([part.strip()] if part.strip() else []), 0
    if not isinstance(part, dict):
        return [], 1
    for key in ("text", "content"):
        value = part.get(key)
        if isinstance(value, str) and value.strip():
            return [value.strip()], 0
        if isinstance(value, list):
            fragments: list[str] = []
            unsupported = 0
            for item in value:
                found, missed = render_part(item)
                fragments.extend(found)
                unsupported += missed
            if fragments:
                return fragments, unsupported
    kind = part.get("content_type") or part.get("type") or "unknown"
    if any(key in part for key in ("asset_pointer", "image_asset_pointer", "audio_asset_pointer")):
        return [f"[non-text attachment omitted: {kind}]"], 0
    return [], 1


def extract_text(content: Any) -> tuple[str, str, int]:
    if not isinstance(content, dict):
        return "", "unknown", 1
    content_type = str(content.get("content_type") or "unknown")
    parts = content.get("parts")
    if not isinstance(parts, list):
        text = content.get("text")
        if isinstance(text, str):
            return text.strip(), content_type, 0
        return "", content_type, 1
    fragments: list[str] = []
    unsupported = 0
    for part in parts:
        found, missed = render_part(part)
        fragments.extend(found)
        unsupported += missed
    return "\n".join(fragment for fragment in fragments if fragment), content_type, unsupported


def selected_node_ids(mapping: dict[str, Any], current_node: Any) -> tuple[list[str], str]:
    if isinstance(current_node, str) and current_node in mapping:
        path: list[str] = []
        seen: set[str] = set()
        cursor: str | None = current_node
        while cursor and cursor in mapping and cursor not in seen:
            seen.add(cursor)
            path.append(cursor)
            parent = mapping[cursor].get("parent") if isinstance(mapping[cursor], dict) else None
            cursor = parent if isinstance(parent, str) else None
        path.reverse()
        return path, "active_branch"

    sortable: list[tuple[float, int, str]] = []
    for index, (node_id, node) in enumerate(mapping.items()):
        message = node.get("message") if isinstance(node, dict) else None
        timestamp = message.get("create_time") if isinstance(message, dict) else None
        sortable.append((float(timestamp) if isinstance(timestamp, (int, float)) else float("inf"), index, node_id))
    sortable.sort()
    return [node_id for _, _, node_id in sortable], "all_nodes_fallback"


def normalize_conversation(conversation: dict[str, Any], number: int) -> tuple[dict[str, Any] | None, dict[str, int | str]]:
    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict):
        return None, {"unsupported_messages": 0, "excluded_branch_messages": 0, "branch_strategy": "missing_mapping"}

    node_ids, strategy = selected_node_ids(mapping, conversation.get("current_node"))
    total_message_nodes = sum(
        1 for node in mapping.values() if isinstance(node, dict) and isinstance(node.get("message"), dict)
    )
    selected_message_nodes = 0
    unsupported = 0
    turns: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    conversation_ref = f"c{number:06d}"

    for node_id in node_ids:
        node = mapping.get(node_id)
        message = node.get("message") if isinstance(node, dict) else None
        if not isinstance(message, dict):
            continue
        selected_message_nodes += 1
        author = message.get("author")
        role = author.get("role") if isinstance(author, dict) else None
        if role not in {"user", "assistant"}:
            continue
        text, content_type, missed = extract_text(message.get("content"))
        unsupported += missed
        if not text:
            continue
        counters[role] += 1
        prefix = "u" if role == "user" else "a"
        turns.append(
            {
                "source_ref": f"{conversation_ref}:{prefix}{counters[role]:04d}",
                "role": role,
                "timestamp": iso_timestamp(message.get("create_time")),
                "content_type": content_type,
                "text": text,
            }
        )

    if not turns or not any(turn["role"] == "user" for turn in turns):
        return None, {
            "unsupported_messages": unsupported,
            "excluded_branch_messages": max(0, total_message_nodes - selected_message_nodes),
            "branch_strategy": strategy,
        }

    record = {
        "schema_version": RECORD_VERSION,
        "conversation_ref": conversation_ref,
        "title": conversation.get("title") or "Untitled conversation",
        "created_at": iso_timestamp(conversation.get("create_time")),
        "updated_at": iso_timestamp(conversation.get("update_time")),
        "branch_strategy": strategy,
        "turns": turns,
    }
    stats: dict[str, int | str] = {
        "unsupported_messages": unsupported,
        "excluded_branch_messages": max(0, total_message_nodes - selected_message_nodes),
        "branch_strategy": strategy,
    }
    return record, stats


def segment_conversation(conversation: dict[str, Any], target_chars: int) -> list[dict[str, Any]]:
    base = {key: value for key, value in conversation.items() if key != "turns"}
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_size = 0
    for turn in conversation["turns"]:
        turn_size = len(json.dumps(turn, ensure_ascii=False)) + 1
        if current and current_size + turn_size > target_chars:
            groups.append(current)
            current = []
            current_size = 0
        current.append(turn)
        current_size += turn_size
    if current:
        groups.append(current)
    total = len(groups)
    return [
        {**base, "segment_index": index, "segment_count": total, "turns": group}
        for index, group in enumerate(groups, 1)
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def prepare(source_path: Path, output: Path, batch_chars: int, max_json_mb: int) -> dict[str, Any]:
    if batch_chars < 20_000:
        raise ValueError("--batch-chars must be at least 20000")
    if max_json_mb < 1:
        raise ValueError("--max-json-mb must be positive")
    if output.exists():
        raise ValueError(f"Output directory already exists: {output}")

    located = locate_source(source_path)
    raw, digest = load_json(located, max_json_mb * 1_048_576)
    conversations: list[dict[str, Any]] = []
    skipped = 0
    unsupported = 0
    excluded_branches = 0
    branch_strategies: Counter[str] = Counter()

    for number, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            skipped += 1
            continue
        record, stats = normalize_conversation(item, number)
        unsupported += int(stats["unsupported_messages"])
        excluded_branches += int(stats["excluded_branch_messages"])
        branch_strategies[str(stats["branch_strategy"])] += 1
        if record is None:
            skipped += 1
        else:
            conversations.append(record)

    if not conversations:
        raise ValueError("No conversations containing user-authored text were found")

    segments = [segment for conversation in conversations for segment in segment_conversation(conversation, batch_chars)]
    batches: list[list[dict[str, Any]]] = []
    current_batch: list[dict[str, Any]] = []
    current_chars = 0
    oversized_segments = 0
    for segment in segments:
        size = len(json.dumps(segment, ensure_ascii=False)) + 1
        if size > batch_chars:
            oversized_segments += 1
        if current_batch and current_chars + size > batch_chars:
            batches.append(current_batch)
            current_batch = []
            current_chars = 0
        current_batch.append(segment)
        current_chars += size
    if current_batch:
        batches.append(current_batch)

    roles = Counter(turn["role"] for conversation in conversations for turn in conversation["turns"])
    user_dates = sorted(
        turn["timestamp"]
        for conversation in conversations
        for turn in conversation["turns"]
        if turn["role"] == "user" and turn["timestamp"]
    )
    undated_user_turns = sum(
        1
        for conversation in conversations
        for turn in conversation["turns"]
        if turn["role"] == "user" and not turn["timestamp"]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".{output.name}.staging-{uuid.uuid4().hex}"
    try:
        (staging / "private" / "batches").mkdir(parents=True)
        (staging / "private" / "checkpoints").mkdir()
        (staging / "public").mkdir()
        write_jsonl(staging / "private" / "corpus.jsonl", conversations)
        for index, batch in enumerate(batches, 1):
            write_jsonl(staging / "private" / "batches" / f"batch-{index:04d}.jsonl", batch)
        manifest = {
            "schema_version": MANIFEST_VERSION,
            "created_at": now_iso(),
            "source": {
                "kind": "zip" if located.zip_member else "json",
                "label": located.label,
                "conversations_sha256": digest,
                "conversations_bytes": located.size,
            },
            "corpus": {
                "raw_conversation_entries": len(raw),
                "active_conversations": len(conversations),
                "skipped_entries": skipped,
                "turns_by_role": dict(sorted(roles.items())),
                "first_user_turn_at": user_dates[0] if user_dates else None,
                "last_user_turn_at": user_dates[-1] if user_dates else None,
                "undated_user_turns": undated_user_turns,
                "excluded_branch_messages": excluded_branches,
                "unsupported_content_parts": unsupported,
                "branch_strategies": dict(sorted(branch_strategies.items())),
            },
            "batching": {
                "target_characters": batch_chars,
                "batch_count": len(batches),
                "segment_count": len(segments),
                "oversized_segments": oversized_segments,
            },
            "privacy": {
                "classification": "highly_sensitive",
                "raw_content_location": "private/",
                "public_directory_contains_raw_content": False,
            },
        }
        write_json(staging / "manifest.json", manifest)
        staging.replace(output)
        return manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    args = parse_args()
    try:
        manifest = prepare(
            args.source.expanduser().resolve(),
            args.out.expanduser().resolve(),
            args.batch_chars,
            args.max_json_mb,
        )
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f"Preparation failed: {error}", file=sys.stderr)
        return 1
    corpus = manifest["corpus"]
    batching = manifest["batching"]
    print(
        f"Prepared {corpus['active_conversations']} conversations and "
        f"{corpus['turns_by_role'].get('user', 0)} user turns in {batching['batch_count']} batches."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
