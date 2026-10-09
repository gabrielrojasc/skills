---
name: codex
description: Hands work to Codex. Use when a task should run in Codex.
---

# Codex

Run a task in Codex with `codex exec`, then open the files it made; its summary
isn't proof. Claude Code allows only unchained `Bash(codex exec:*)` calls, so
run each command exactly as shown.

```bash
codex exec --approve-for-me --skip-git-repo-check -C <dir> -o <out>/final.md - < <out>/prompt.md > <out>/run.log 2>&1
```

- `-C` is the sandbox root: the repository for code work, otherwise a new
  folder outside git.
- Pass the prompt on stdin, or inline with `< /dev/null`. End it with "Don't
  ask questions; if something blocks you, say what and stop."
- Run tasks longer than 10 minutes in the background. A background run dies
  with the Claude Code session and after about 30 minutes.

Follow up in the same session, from the log's `session id:` line. Options go
before `resume`, and `-C` is required again:

```bash
codex exec --approve-for-me --skip-git-repo-check -C <dir> -o <out>/final-2.md resume <session-id> "<next instruction>" < /dev/null > <out>/run-2.log 2>&1
```

## Browser and desktop apps

- Use `@Chrome` for websites, even when the user says computer use. It drives
  the user's signed-in Chromium browser, such as Helium, in new tabs, never a
  new window. Name the browser in the prompt; the plugin's diagnostic scripts
  only know Chrome. Downloads need "Ask where to save each file" off.
- Computer Use drives native apps and takes over the cursor.
- Keep live accounts read-only unless the user approves a write.
- Each app, and each site's hover, resize, or device emulation, needs the
  user's approval once per session. When Codex reports it wasn't approved, ask
  the user to run `codex resume <session-id>`, approve, and `/exit`, then
  continue the session.

Leave Codex's approval records alone, and never use
`--dangerously-bypass-approvals-and-sandbox`.
