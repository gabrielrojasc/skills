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
   word. Tell Codex to use its Google Drive connector only, with no browser or
   shell, and to make every change in one `batchUpdate` call that sets the tab
   ID on each edit and `requiredRevisionId` to the revision it read.
2. Call `read_file_content` and report what each changed tab now says.
