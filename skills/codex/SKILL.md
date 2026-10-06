---
name: codex
description: Hands work to Codex. Use when a task should run in Codex.
---

# Codex

Run a task in Codex from Claude Code with `codex exec`, then check what it
produced: a second opinion, work the user asks to give Codex, or browser and
desktop-app work. Claude Code needs the `Bash(codex exec:*)` allow rule; if
it's missing, ask the user to add it.

## Run a task

Run one unchained command, so the allow rule covers it:

```bash
codex exec --approve-for-me --skip-git-repo-check -C <dir> -o <out>/final.md - < <out>/prompt.md > <out>/run.log 2>&1
```

- `--approve-for-me` sends Codex's approval requests to its automatic reviewer,
  so nothing waits on the user.
- `-C <dir>` is Codex's working directory and sandbox root: it writes there and
  in temp directories without escalating. Point it at the repository for code
  work, or at a new folder outside git otherwise.
- Pass the prompt on stdin from a file, or inline in quotes with
  `< /dev/null`. Name skills in it ("Use the code-review skill on ...").
  End it with "Don't ask questions; if something blocks you, say what and
  stop," since `codex exec` can't take replies.
- The final message lands in `-o`, and the session ID on the `session id:` line
  of the log.
- Run short tasks in the foreground with a 10-minute timeout. Run longer ones,
  such as reviews, in the background; a background run dies with the Claude
  Code session and after about 30 minutes.

## Follow up

Continue the same session, passing `-C` again and putting options before
`resume`:

```bash
codex exec --approve-for-me --skip-git-repo-check -C <dir> -o <out>/final-2.md resume <session-id> "<next instruction>" < /dev/null > <out>/run-2.log 2>&1
```

Only one process can write to a session; an open interactive `codex resume`
blocks it.

## Browser and desktop apps

- **`@Chrome`** drives the user's signed-in Chrome in a background tab group.
  Downloads need Chrome's "Ask where to save each file" off.
- **Computer Use** drives native apps and takes over the cursor.
- Keep live accounts read-only unless the user approves a write. Leave out
  moving the pointer without a click, resizing the viewport, and device
  emulation: they need a per-site approval `codex exec` can't give.
- Each app needs the user's approval once per session. When Codex reports it
  "was not approved to use <App>" or that "the permission request was
  dismissed", ask the user to run `codex resume <session-id>`, approve, and
  `/exit`, then continue the session.

## Check

Read the final message and open the files Codex made; its summary isn't proof.
Leave Codex's approval records alone, and never use
`--dangerously-bypass-approvals-and-sandbox`.
