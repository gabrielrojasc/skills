---
name: slack-message
description: Use when drafting a Slack message.
---

# Slack message

Format text I'll paste into Slack with Slack markup:

- `*bold*`, `_italic_`, `~strike~`
- `` `code` `` and triple-backtick blocks
- `>` for quotes
- `[text](url)` for links
- No headings or tables. Use a bold line or a `-` list instead.

Return the message in a code block so the terminal doesn't render it.

When you post through the Slack connector, use the standard Markdown its tools
ask for instead.

## Voice

Write it the way I'd type it in the thread, not as a report. Where this
disagrees with the Writing section of my `AGENTS.md`, follow this section.

- Don't restate what the other person just said or quoted.
- Ask at most three questions, and only ones the recipient alone can answer.
  For anything else, propose a default or leave it for later.
- Ask questions in plain sentences, not a list, unless I ask for one.
- When the thread has messages from me, match their length.
