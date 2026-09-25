# Insight and evidence system

Use this reference after batch checkpoints exist and before writing a profile, focused recipe result, card, or public copy.

## Memory ladder

```text
private/corpus.jsonl
  → session-memories.jsonl
  → theme-time-map.json
  → insights.jsonl
  → profile, reports, cards, and public package
```

Each layer must preserve opaque pointers to the prior layer. The lower layers remain authoritative. Compression is for retrieval and synthesis, never a reason to discard counterevidence or source context.

## Session memory and theme/time map

A session memory is neutral and non-diagnostic: a conversation/segment reference, date range, source references, short contextual summary, candidate themes, explicit decisions/events, open questions, contamination warnings, and incompleteness flag. Do not turn a question, copied text, assistant suggestion, or isolated event into a personality attribute.

The theme/time map groups independent session-memory IDs and date periods. It may call a theme persistent, rising, declining, context-shifted, or too sparse to characterize; it must not infer causality from frequency.

## Evidence-engine protocol

For every recipe dimension:

1. Translate it into a neutral, observable question.
2. Retrieve candidate session memories by theme and time, then inspect the referenced user turns in context.
3. Count independent contexts, not message volume. A long thread is one context.
4. Search deliberately for counterevidence and boundary cases.
5. Compare coverage with recipe minimums. If insufficient, emit `insufficient_evidence` rather than a weak positive conclusion.
6. Record an atomic insight: recipe and dimension, claim type, scope, coverage, support, counterevidence, contamination, sensitivity, disconfirmation condition, and calibration status.

Scores are explanatory rankings, not psychometric measurements. Do not use them to rank people or make clinical, protected-trait, relationship, financial, political, or other restricted inferences.

## Insight → presentation

An Insight is the only reusable unit allowed to move from analysis into a profile or renderer. A renderer may shorten, reorder, select tone, or choose visual layout, but cannot increase confidence, hide relevant limits, invent facts, or turn an editorial hypothesis into an observation. Public output may use only accepted or edited, non-`keep_private` insights and contains no source pointers, excerpts, raw dates, or private analysis metadata.
