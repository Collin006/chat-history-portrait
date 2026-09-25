#!/usr/bin/env python3
"""Run dependency-free integration tests for the skill's deterministic tools."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PREPARE = SCRIPT_DIR / "prepare_chat_history.py"
VALIDATE = SCRIPT_DIR / "validate_profile_package.py"
SCAN = SCRIPT_DIR / "scan_public_output.py"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def checkpoint(batch_id: str, refs: list[str]) -> dict[str, object]:
    return {
        "schema_version": "portrait-checkpoint/1.0",
        "batch_id": batch_id,
        "claims": [],
        "experiences": [],
        "themes": [],
        "tensions": [],
        "content_seeds": [],
        "contamination_warnings": [],
        "processed_source_refs": refs,
        "completed_at": "2026-01-01T00:00:00Z",
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="portrait-self-test-") as temp:
        root = Path(temp)
        source = root / "conversations.json"
        workspace = root / "workspace"
        conversations = [
            {
                "id": "raw-id-1",
                "title": "Private title",
                "create_time": 1_700_000_000,
                "update_time": 1_700_000_400,
                "current_node": "a2",
                "mapping": {
                    "root": {"id": "root", "parent": None, "message": None},
                    "u1": {
                        "id": "u1",
                        "parent": "root",
                        "message": {"author": {"role": "user"}, "create_time": 1_700_000_100, "content": {"content_type": "text", "parts": ["I return to projects after collecting examples."]}},
                    },
                    "a1": {
                        "id": "a1",
                        "parent": "u1",
                        "message": {"author": {"role": "assistant"}, "create_time": 1_700_000_200, "content": {"content_type": "text", "parts": ["Context reply"]}},
                    },
                    "u-alt": {
                        "id": "u-alt",
                        "parent": "u1",
                        "message": {"author": {"role": "user"}, "create_time": 1_700_000_250, "content": {"content_type": "text", "parts": ["This abandoned branch must be excluded."]}},
                    },
                    "a2": {
                        "id": "a2",
                        "parent": "a1",
                        "message": {"author": {"role": "assistant"}, "create_time": 1_700_000_300, "content": {"content_type": "text", "parts": ["Active reply"]}},
                    },
                },
            },
            {
                "id": "raw-id-2",
                "title": "Second context",
                "create_time": 1_700_100_000,
                "current_node": "b2",
                "mapping": {
                    "b1": {
                        "id": "b1",
                        "parent": None,
                        "message": {"author": {"role": "user"}, "create_time": 1_700_100_100, "content": {"content_type": "text", "parts": ["Examples help me resume difficult work."]}},
                    },
                    "b2": {
                        "id": "b2",
                        "parent": "b1",
                        "message": {"author": {"role": "assistant"}, "create_time": 1_700_100_200, "content": {"content_type": "text", "parts": ["Another reply"]}},
                    },
                },
            },
        ]
        write_json(source, conversations)
        prepared = run(sys.executable, str(PREPARE), str(source), "--out", str(workspace), "--batch-chars", "20000")
        assert prepared.returncode == 0, prepared.stderr
        manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["corpus"]["active_conversations"] == 2
        assert manifest["corpus"]["excluded_branch_messages"] == 1
        corpus_text = (workspace / "private" / "corpus.jsonl").read_text(encoding="utf-8")
        assert "abandoned branch" not in corpus_text
        assert "c000001:u0001" in corpus_text and "c000002:u0001" in corpus_text

        export_zip = root / "export.zip"
        zip_workspace = root / "zip-workspace"
        with zipfile.ZipFile(export_zip, "w") as archive:
            archive.write(source, "nested/conversations.json")
        zip_prepared = run(sys.executable, str(PREPARE), str(export_zip), "--out", str(zip_workspace), "--batch-chars", "20000")
        assert zip_prepared.returncode == 0, zip_prepared.stderr
        zip_manifest = json.loads((zip_workspace / "manifest.json").read_text(encoding="utf-8"))
        assert zip_manifest["source"]["kind"] == "zip"
        assert zip_manifest["source"]["conversations_sha256"] == manifest["source"]["conversations_sha256"]

        for batch_path in sorted((workspace / "private" / "batches").glob("batch-*.jsonl")):
            refs: list[str] = []
            for line in batch_path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                refs.extend(turn["source_ref"] for turn in record["turns"] if turn["role"] == "user")
            write_json(workspace / "private" / "checkpoints" / f"{batch_path.stem}.analysis.json", checkpoint(batch_path.stem, refs))

        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        private_profile = {
            "schema_version": "portrait-private/1.0",
            "profile_id": "test-profile",
            "generated_at": timestamp,
            "corpus": {"manifest_schema": "chat-history-corpus/1.0", "conversation_count": 2, "user_turn_count": 2, "batch_count": manifest["batching"]["batch_count"]},
            "claims": [{
                "claim_id": "clm_001",
                "claim_type": "observed_pattern",
                "text": "The user often uses examples to resume difficult work.",
                "confidence": 0.72,
                "support": [
                    {"source_ref": "c000001:u0001", "reason": "Explicit behavior"},
                    {"source_ref": "c000002:u0001", "reason": "Independent recurrence"},
                ],
                "counterevidence": [],
                "sensitivity": "low",
                "disconfirmation": "Repeated examples of resuming without research",
                "status": "accepted",
            }],
            "timeline": [],
            "themes": [],
            "tensions": [],
            "story_material": [],
            "limitations": ["Synthetic test corpus"],
        }
        write_json(workspace / "private" / "profile.json", private_profile)
        calibration = {
            "schema_version": "portrait-calibration/1.0",
            "reviewed_at": timestamp,
            "decisions": [{"claim_id": "clm_001", "decision": "accept", "replacement": None, "note": None}],
            "global_notes": [],
            "public_consent": True,
            "audience": "public",
            "identity_mode": "anonymous",
            "off_limits": [],
        }
        write_json(workspace / "private" / "calibration.json", calibration)
        public_profile = {
            "schema_version": "portrait-public/1.0",
            "profile_id": "test-profile",
            "generated_at": timestamp,
            "language": "en",
            "audience": "public",
            "identity_mode": "anonymous",
            "display": {"name": None, "headline": "The example collector", "summary": "Examples are a way back into hard work."},
            "patterns": [{"title": "Collect, then return", "body": "A recurring working rhythm."}],
            "tension": {"title": "Pause and persistence", "body": "Stepping back can support returning."},
            "change": None,
            "open_question": "Which example is enough to begin again?",
            "story_angles": [],
            "share_cards": [],
            "scope_note": "A partial reading of conversation history, not a complete identity.",
            "consent": {"approved": True, "approved_at": timestamp, "off_limits_applied": True},
            "provenance": {"generator": "chat-history-portrait", "corpus_digest_prefix": manifest["source"]["conversations_sha256"][:12]},
        }
        write_json(workspace / "public" / "profile.json", public_profile)
        write_json(workspace / "public" / "site-package.json", public_profile)

        validated = run(sys.executable, str(VALIDATE), str(workspace), "--stage", "all")
        assert validated.returncode == 0, validated.stderr
        scanned = run(sys.executable, str(SCAN), str(workspace / "public"))
        assert scanned.returncode == 0, scanned.stderr
        report = json.loads((workspace / "public" / "privacy-scan.json").read_text(encoding="utf-8"))
        assert report["status"] == "no_automated_findings", report

        leak = workspace / "public" / "share-cards.md"
        leak.write_text("Contact person@example.com for the private version.\n", encoding="utf-8")
        leak_scan = run(sys.executable, str(SCAN), str(workspace / "public"), "--fail-on-findings")
        assert leak_scan.returncode == 3, leak_scan.stderr
        leak_report = json.loads((workspace / "public" / "privacy-scan.json").read_text(encoding="utf-8"))
        assert any(item["kind"] == "email" for item in leak_report["findings"])
    print("All chat-history-portrait self-tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
