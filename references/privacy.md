# Privacy and consent protocol

Use this reference before any public-facing artifact is drafted.

## Data zones

- **Raw zone:** original export. Read-only; never copied into public output.
- **Private zone:** normalized corpus, checkpoints, excerpts, source references, evidence ledger, corrections, and full portrait.
- **Public zone:** generalized, user-approved content with no raw evidence or hidden metadata.

The existence of a detail in the export is not consent to publish it.

## Sensitivity levels

- `low`: general interests, broad working habits, non-identifying preferences.
- `medium`: career direction, approximate life phase, emotionally revealing patterns, uncommon combinations of facts.
- `high`: relationships, employers/schools, exact places/dates, finances, legal matters, health, conflict, intimate experiences.
- `restricted`: credentials, account data, government identifiers, contact information, third-party secrets, minors, or details the user marks off-limits.

Restricted material never enters public output. High-sensitivity material requires explicit item-level approval and should still be generalized where possible.

## Disclosure modes

| Mode | Identity | Dates and places | Life events | Quotations |
| --- | --- | --- | --- | --- |
| `anonymous` | no real name or handles | remove or heavily generalize | include only broad, approved themes | none |
| `pseudonymous` | chosen display name | generalize | approved events with identifying edges removed | paraphrase only |
| `named` | user-approved name | retain only item-level approved details | item-level approval | short paraphrase preferred |

Third-party personal information is removed in every mode unless that person has independently consented; the subject cannot consent for them.

## Public-output review

Before finalization:

1. Generate public copy only from accepted/edited, non-private claims.
2. Remove source references, excerpts, conversation titles, raw timestamps, filenames, account identifiers, and hidden metadata.
3. Run `scan_public_output.py`.
4. Review flagged email, phone, handle, URL, IP address, precise date, government-ID-like, and long-number patterns.
5. Manually review names, locations, organizations, rare anecdotes, relationship details, health, legal, financial, political, religious, sexual, and minor-related content; deterministic scanners cannot reliably detect these.
6. Show the user the final public package and the privacy report. Record approval; do not infer it from earlier enthusiasm.

## Website handoff

The website package contains only public-schema fields. Never include the raw source hash; use an optional short non-reversible prefix only for local version comparison. Do not send cookies, ChatGPT account data, export filenames, conversation IDs, or evidence pointers.

Creating the local package and uploading it are separate actions. Ask for authorization immediately before the first upload or account-linking action, and state exactly which file will be sent.
