---
name: computer-use
description: Use when a task needs a signed-in site or a Mac app.
---

# Computer use

T3's preview tools cover public websites. Use this skill for the user's
signed-in browser and for native apps.

- Keep live accounts read-only unless the user approves a write.
- Each native app needs the user's approval once per session.

## Claude

- Use the Claude in Chrome tools (`mcp__claude-in-chrome__*`) for the browser.
  They work in their own tab group.
- Hand native apps to Codex with `delegate_task` at the chosen rung, and ask
  for Computer Use. Then open what Codex produced; its summary isn't proof.

## Codex

- For the browser, call `setupBrowserRuntime()` from
  `~/.codex/plugins/cache/openai-bundled/chrome/latest/scripts/browser-client.mjs`
  in `cua_repl` and use the `extension` browser. It reports itself as Chrome
  whichever browser it is.
- Use Computer Use for native apps. It takes over the cursor. Leave Codex's
  approval records alone.
