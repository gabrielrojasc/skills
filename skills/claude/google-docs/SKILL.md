---
name: google-docs
description: Use when a task writes to a Google Doc.
---

# Google Docs

Hand every Google Docs write to Codex. Claude's Google Drive connector can read
every tab, but its only write tool, `update_file`, replaces the whole file.
Codex's Google Drive connector calls the Docs API `batchUpdate`, which can edit
a single tab.

The doc ID is the part of the URL after `/document/d/`.

## Read

Call `read_file_content` with the doc ID. It returns each tab under a
`# <tab title>` heading.

## Write

1. Delegate the edit to Codex with `delegate_task` at the `proven` rung. In the
   brief, give the doc ID, the edit, and the user's approval quoted word for
   word. Tell Codex to:
   - Use MCP tools only, with no browser or shell.
   - Call `mcp__codex_apps__google_drive_get_document` to get the tab IDs and
     the `revisionId`.
   - Make every change in one
     `mcp__codex_apps__google_drive_batch_update_document` call. Set
     `location.tabId` on each text edit, use `addDocumentTab` to create tabs,
     and set `write_control.requiredRevisionId` to the revision it read. If
     someone else edits the doc first, the call fails instead of overwriting
     their change.
   - End by quoting the `mcp__codex_apps__google_drive_get_document_text`
     output for every tab it changed.
2. Check that Codex's quoted read-back matches the edit you asked for. Then
   call `read_file_content` yourself and report what each changed tab now says.
