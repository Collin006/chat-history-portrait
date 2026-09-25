# Chat History Portrait

Turn an official ChatGPT data export into an evidence-grounded private portrait, then—only if the user chooses—into a deliberately redacted shareable identity package.

This is a [Codex Skill](https://developers.openai.com/codex/skills/) for people who want to understand long-running patterns in their own conversation history: recurring questions, working style, changes over time, creative threads, and story-worthy tensions.

It is **not** a personality test, a diagnosis tool, or a cloud chat-history uploader.

## What it does

- Reads an official ChatGPT export ZIP, extracted export directory, or `conversations.json` locally.
- Reconstructs active branches, assigns opaque source references, creates bounded batches, and supports resumable analysis.
- Separates directly stated facts, observed long-term patterns, and editorial hypotheses.
- Requires supporting evidence, counterevidence, confidence, and a disconfirmation condition for important claims.
- Builds a private portrait first, then records user decisions such as accept, edit, reject, or keep private.
- Offers a recipe catalog for focused outputs such as an annual version note, recurring questions, working style, productive contradictions, interest evolution, and unfinished work.
- Produces a validated, privacy-scanned public package only after explicit approval.

## Privacy model

Raw exports, normalized corpora, source references, private evidence, and private reports stay on the local machine. The public package is a separate, redacted artifact and contains no raw excerpts, source pointers, conversation titles, or private timestamps.

Only user-authored messages are evidence about the user. Assistant messages may provide conversational context but never count as biographical proof.

## Install

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/Collin006/chat-history-portrait.git ~/.codex/skills/chat-history-portrait
```

Then invoke it in Codex:

```text
Use $chat-history-portrait to analyze my ChatGPT export locally and build an evidence-grounded private portrait.
```

## Quick start

1. Request a data export from ChatGPT and download the ZIP when it arrives.
2. Provide the ZIP, extracted directory, or `conversations.json` to Codex with an unused local output directory.
3. The Skill runs the preparer:

```bash
python3 scripts/prepare_chat_history.py /path/to/export.zip --out /path/to/private-workspace
```

4. Review the private portrait and calibrate its claims.
5. If desired, choose a disclosure level and generate a shareable package locally.

The full workflow lives in [SKILL.md](SKILL.md). Start with [the recipe catalog](recipes/CATALOG.md) for available questions and formats.

## Repository layout

```text
SKILL.md                 Core workflow and safety boundaries
recipes/                 Built-in analysis recipe declarations and catalog
references/              Evidence, privacy, schema, and workflow guidance
scripts/                 Local corpus preparation and validation tools
```

## Validation

The deterministic helpers have no third-party Python dependency:

```bash
python3 scripts/validate_recipes.py
python3 scripts/self_test.py
```

## Contribution principles

New recipes and renderers are welcome, but they must preserve the core model:

- Never infer a sensitive trait, diagnosis, or private event from indirect chat evidence.
- Treat insufficient evidence as a valid result.
- Do not place source references, raw excerpts, or third-party details in public output.
- Do not make a recipe automatically publish or upload a result.

## Status

The Skill is in active development. It currently supports official ChatGPT exports and local, evidence-grounded portrait generation. Website integration, incremental yearly imports, and community recipe publishing are future work.
