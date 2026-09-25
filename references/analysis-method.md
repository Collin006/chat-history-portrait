# Analysis method

Use this reference while producing batch checkpoints, the evidence ledger, and the private profile.

## Unit of evidence

The atomic evidence unit is a user-authored turn with an opaque source reference. Interpret it in its conversation context, but do not treat assistant text as evidence. Distinct repetitions require different conversations or meaningfully separated time periods.

Classify every candidate:

| Type | Standard | Appropriate wording |
| --- | --- | --- |
| `stated_fact` | User explicitly describes an experience, preference, decision, or identity-relevant fact. | “The user states…” |
| `observed_pattern` | Similar behavior or concern recurs across independent contexts, with counterevidence considered. | “Across several contexts, the record suggests…” |
| `editorial_hypothesis` | A coherent interpretation that could organize the material but is not established. | “One possible reading is…” |

Questions are not admissions. Requests to rewrite, translate, simulate, research, or advise another person are not autobiographical unless the user explicitly connects them to themselves.

## Confidence rubric

Use confidence to expose uncertainty, not to manufacture scientific precision.

- **0.85–1.00:** directly stated, unambiguous, and not contradicted; or a strongly repeated behavioral pattern across time and contexts.
- **0.65–0.84:** multiple independent supports with limited ambiguity or meaningful counterevidence.
- **0.45–0.64:** plausible but context-bound; retain privately as a question or hypothesis.
- **Below 0.45:** do not include as a profile conclusion. It may remain as an investigation prompt.

Reduce confidence for copied material, role-play, ambiguous pronouns, third-party tasks, translation, hypotheticals, contradictions, tightly clustered repetitions, or missing temporal context.

## Required claim fields

Every claim must include:

- concise neutral text
- claim type and confidence
- supporting source references with a reason for each
- counterevidence or an explicit note that none was found
- sensitivity: `low`, `medium`, `high`, or `restricted`
- a disconfirmation condition: what new evidence would weaken or reverse it
- status from user calibration

Avoid labels that merely flatter. Prefer observable formulations such as “revises plans after gathering examples” over abstractions such as “visionary.”

## Longitudinal analysis

Divide the dated corpus into meaningful periods based on actual density and transitions, not arbitrary equal buckets. For each theme, distinguish:

- persistent pattern
- rising or declining concern
- one-time episode
- phase transition
- apparent contradiction caused by changing context

Do not turn absence of discussion into evidence that something stopped mattering.

## Life experiences and chronology

Add an experience to the timeline only when the user explicitly describes it. Separate:

- dated event
- approximate-period event
- undated experience
- intended future event

Plans are not completed events. Advice sought about an event is not proof it occurred. When two sources conflict, show the conflict.

## Personality boundary

Describe conversational and decision patterns rather than clinical or psychometric diagnoses. Named personality systems may be used only as playful, user-requested lenses, clearly labeled non-diagnostic. Never infer health status, trauma, sexuality, religion, ethnicity, political affiliation, or other sensitive traits from indirect clues.

## Coverage check

Before synthesis, verify:

- every batch has a checkpoint
- high-confidence patterns span independent contexts
- vivid but isolated anecdotes are not overweighted
- negative and positive counterexamples were sought
- changes over time were evaluated
- third-party and fictional material were excluded
- corpus limitations are explicit
