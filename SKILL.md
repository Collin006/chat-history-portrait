---
name: chat-history-portrait
description: Turn an official ChatGPT data export into an evidence-grounded private portrait and optional shareable identity package. Use when a user wants personality patterns, life themes, timelines, entertaining story angles, social cards, or a website-ready profile derived from their full conversation history. Keep raw history local, separate facts from interpretation, and never publish or upload without explicit approval.
metadata:
  version: "1.2.0"
  public_schema: "portrait-public/1.0"
---

# Chat History Portrait

Build a compelling, auditable portrait from a user's ChatGPT history. The product is not a generic summary: it is a private self-understanding report plus an optional, deliberately redacted social object that other people would want to read and create for themselves.

## Non-negotiable boundaries

- Treat the export, normalized corpus, checkpoints, evidence ledger, and private report as highly sensitive local data.
- Never upload raw conversations, private artifacts, excerpts, or a website package unless the user explicitly requests that specific external action.
- Treat only user-authored messages as evidence about the user. Assistant text supplies context, never biographical proof.
- Do not diagnose, reveal protected traits, or turn uncertain inferences into facts. Do not infer a private event merely because the user asked about it.
- Do not optimize virality by exposing vulnerability, third-party information, or uniquely identifying anecdotes.
- Keep evidence-bearing private artifacts and public artifacts in separate directories. Public files must contain no source pointers or raw excerpts.

## Choose the mode

- **Private portrait** is the default: prepare the corpus, analyze every batch, synthesize a private report, and invite corrections.
- **Shareable package** adds entertaining public copy and a website-ready JSON package. Enter this mode only after the user selects an audience and disclosure level and approves the underlying portrait.
- **Rework** uses an existing workspace plus user corrections. Preserve rejected claims and correction history so they do not silently return.

## Choose an analysis recipe

The private portrait is the baseline recipe. For a focused question, first browse [recipes/CATALOG.md](recipes/CATALOG.md), then use its matching built-in declaration under `recipes/` or create a temporary declaration that follows the recipe system. Read [references/recipe-system.md](references/recipe-system.md) before running a focused recipe.

Recipes specify questions, minimum independent contexts, desired longitudinal coverage, and output shape. They do not override evidence, privacy, or calibration rules. If their evidence threshold cannot be met, return an insufficiency or editorial question rather than forcing a conclusion. Do not run a community recipe that requests restricted traits, raw excerpts, or an unapproved public upload.

## Prepare the corpus

Ask for the official export ZIP, its extracted directory, or `conversations.json`, plus an unused output directory. Then run:

```bash
python3 scripts/prepare_chat_history.py SOURCE --out OUTPUT
```

The preparer selects the active branch of branched conversations, assigns opaque source references, builds bounded batches, records a source digest, and writes atomically. Do not improvise a different parser when this script supports the input. If preparation fails or reports an unsupported shape, explain the specific issue and stop.

## Export waiting and annual refresh

When a user wants a portrait but has not yet obtained an export, treat this as an active import task rather than an abandoned prerequisite. Direct them to request the official ChatGPT data export, then create a daily in-thread reminder to check for the export email. This is a user-initiated, short-lived task reminder: default to one reminder per day and do not automatically reduce its frequency.

The reminder ends when the user confirms the file is downloaded, provides an export, or preparation succeeds; the user may also cancel it. Do not claim that an email has arrived unless an explicitly authorized email integration reports it. If such an integration is available and authorized, replace the inbox-check reminder with a direct “export is ready to download” notification, then end the daily reminder.

After a successful portrait, offer an annual refresh reminder for December or a user-chosen date. That reminder starts the same daily export-waiting state after the user requests a new export. Treat a later official export as a new complete snapshot: preserve prior work and compare/deduplicate before producing an updated portrait, rather than assuming the new file contains only one year's conversations or overwriting prior conclusions. Read [references/export-reminders.md](references/export-reminders.md) when creating, resuming, or ending this workflow.

Read [references/workflow.md](references/workflow.md) after preparation. Follow its artifact layout and checkpoint protocol; analyze all batches instead of sampling silently or attempting a one-pass summary.

## Analyze and synthesize

Read [references/analysis-method.md](references/analysis-method.md) before analyzing batches. Each claim must be one of:

- `stated_fact`: explicit autobiographical information, supported by at least one source reference.
- `observed_pattern`: a repeated behavior or preference, supported by distinct conversations or time periods and accompanied by counterevidence.
- `editorial_hypothesis`: a useful interpretation or framing, clearly presented as provisional.

Use opaque references such as `c000123:u0004`; titles and quotations belong only in the private evidence ledger. Weight longitudinal recurrence and behavioral examples more heavily than message volume. Treat role-play, translation, pasted text, hypothetical questions, and tasks performed for other people as contamination risks.

Build the reusable analysis layer in this order: raw transcript → session memories → theme/time map → atomic insights → profile and presentation. Read [references/insight-system.md](references/insight-system.md) for the required memory and evidence-engine protocol. An insight is an atomic, evidence-backed claim that may be reused by multiple recipes and renderers; never let a card or report create a new unsupported claim.

The private portrait must cover corpus limitations, life experiences explicitly stated, recurring motives, working and decision patterns, changes over time, tensions, counter-patterns, open questions, and high-potential story material. Every important conclusion needs confidence, support, and a disconfirmation condition. Show the user the portrait for calibration and record accepted, edited, rejected, and “keep private” decisions.

## Create shareable material

Before public drafting, obtain these choices:

- audience: `private`, `close_circle`, or `public`
- identity: `anonymous`, `pseudonymous`, or `named`
- tone: infer from the corpus, or use the user's specified tone
- topics or people that are off-limits

Read [references/editorial-framework.md](references/editorial-framework.md) to turn approved findings into hooks, story angles, cards, and posts. Entertainment must come from recognition, surprise, tension, specificity, or play—not fabricated certainty.

Read [references/privacy.md](references/privacy.md) before writing public files. Generate the public package using [references/public-profile.schema.json](references/public-profile.schema.json). Run both gates:

```bash
python3 scripts/validate_profile_package.py OUTPUT
python3 scripts/scan_public_output.py OUTPUT/public
```

Any validator error blocks delivery. Privacy findings require review; never mark them safe automatically. The user must approve the final public package after seeing what was removed or generalized.

## Required artifacts

The workspace contract is defined in [references/workflow.md](references/workflow.md). A complete private run contains:

- immutable import manifest and normalized corpus
- one checkpoint per batch
- evidence ledger with auditable source references
- reusable session memories, theme/time map, and atomic insights under `private/analysis/`
- structured private profile conforming to [references/private-profile.schema.json](references/private-profile.schema.json)
- readable private report and user calibration record

A complete shareable run additionally contains:

- redacted public profile JSON
- public story-angle and share-card copy
- privacy scan report
- website handoff package conforming to the same public schema version

Do not invent a website URL or imply affiliation with ChatGPT/OpenAI. If the user later supplies a website endpoint, package locally first and request separate authorization before upload.

## Quality bar

A result is not production-ready if it could plausibly describe most people, relies on one vivid conversation, hides contradictory evidence, exposes private source material, or produces only flattering labels. A strong result makes the subject say “I recognize that pattern,” gives a skeptical reader enough evidence to trust it, and gives an audience a reason to keep reading without violating the subject's privacy.
