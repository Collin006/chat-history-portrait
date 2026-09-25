# Export waiting and refresh reminders

## State model

```text
awaiting_export_request
  → awaiting_export_email
  → export_ready_to_download
  → source_received
  → prepared
  → analyzed
```

The Skill normally begins at `awaiting_export_email` after the user requests an official export. The task owns one daily reminder: “Check whether your ChatGPT data export email has arrived. When you have downloaded the ZIP, return here and attach or provide it so we can begin.”

## Reminder behavior

- Create a thread-attached recurring reminder, once daily, only for an active user-requested export workflow.
- Daily cadence is deliberate: the user is waiting for a prerequisite they explicitly initiated. Do not silently downgrade it.
- End the reminder immediately when a compatible ZIP, extracted export directory, or `conversations.json` is provided; also end it on explicit cancel.
- Do not inspect an inbox or infer delivery from elapsed time. With a separately authorized email integration, delivery can transition the state to `export_ready_to_download` and end the inbox-check reminder.
- Do not make the reminder message contain private history, source paths, or any derived profile information.

## Annual refresh

After the first successful analysis, offer a December or user-selected annual reminder. Its reminder text should ask the user to request a fresh official export and explain that a complete latest snapshot is expected. When the user begins that refresh, create the same daily waiting reminder.

An annual refresh is an update, not a replacement. Preserve the earlier workspace and calibration history; identify already imported conversations by stable source identity and content digest before calculating new material and changes over time. If incremental comparison is unavailable, create a new private workspace and clearly label it as a new snapshot rather than overwriting an old portrait.
