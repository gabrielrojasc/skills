---
name: slack-message
description: Use when drafting a Slack message.
---

# Slack message

Apply the `unslop` skill and the Writing section of my `AGENTS.md`.

Format text I'll paste into Slack with Slack markup:

- `*bold*`, `_italic_`, `~strike~`
- `` `code` `` and triple-backtick blocks
- `>` for quotes
- `[text](url)` for links
- No headings or tables. Use a bold line or a `-` list instead.

Return the message in a code block so the terminal doesn't render it.

When you post through the Slack connector, use the standard Markdown its tools
ask for instead.
