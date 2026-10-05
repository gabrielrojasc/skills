---
name: codex-computer-use
description: Runs GUI tasks via Codex. Use when work needs a browser or app.
---

# Codex computer use

Hand browser and desktop-app work to Codex with `codex exec`, then check what it
produced. Codex has two routes:

- **`@Chrome`** drives the user's signed-in Chrome in its own background tab
  group. Use it for web apps and sites.
- **Computer Use** drives native macOS apps through the screen and takes over
  the cursor while it works. Each app needs the user's approval once per Codex
  session.

## 1. Check the prerequisites

- Claude Code allows `Bash(codex exec:*)` in the user's settings. Without the
  rule, auto mode blocks the launch. Ask the user to add it, and treat a denial
  as final.
- For `@Chrome`, the Codex Chrome extension shows "Connected". For downloads,
  Chrome's "Ask where to save each file" is off; Codex can't answer that dialog.

## 2. Write the brief

Agree the scope with the user first: the site or app, the actions, and the
output folder. Treat live accounts as read-only unless the user approves a
specific write, naming the site and the action.

Write the brief to `<dir>/brief.md`, where `<dir>` is a new folder outside any
git repository, such as `~/tmp/<task>/`:

- the route (`@Chrome` or Computer Use) and the starting page or app;
- the allowed actions, and the actions it must not take;
- every file to save, with its path in `<dir>`;
- "Don't ask questions. If something blocks you, write exactly what blocked you
  and stop." `codex exec` can't receive replies, so a question ends the run.
- For `@Chrome`, the actions plain browsing covers: navigating, clicking,
  typing, scrolling, and screenshots (PNG or JPEG). Moving the pointer without
  a click, resizing the viewport, and device emulation go through raw CDP, which
  needs a per-site approval that `codex exec` can't give; leave them out, or get
  the approval first as in step 4. Codex's cursor can show in screenshots taken
  after a click, so crop or cover it afterwards when the image is for reuse.
- For a set of screenshots meant to match, keep the window size fixed for the
  whole run.

## 3. Launch it

Run each command below exactly as written, as its own call with nothing chained
before or after it, so the allow rule covers it. A chained command such as
`; echo $?` goes to the auto-mode classifier instead, which may deny it. Run it
in the foreground with a 10-minute timeout, and split longer work into briefs
that each fit. A background run dies with the Claude Code session that started it, and
Claude Code stops background tasks after about 30 minutes.

```bash
codex exec --approve-for-me --skip-git-repo-check -C <dir> -o <dir>/final.md - < <dir>/brief.md > <dir>/run.log 2>&1
```

`--approve-for-me` routes Codex's own approvals through its automatic reviewer,
so commands run without prompts. The session ID is on the `session id:` line of
`run.log`.

## 4. Follow up in the same session

Site and app approvals belong to the session, so continue it instead of
starting a new one. Options go before `resume`, and `-C` is required again;
without it the sandbox root becomes your working directory and writes fail with
`EPERM`:

```bash
codex exec --approve-for-me --skip-git-repo-check -C <dir> -o <dir>/final.md resume <session-id> "<next instruction>" < /dev/null > <dir>/run-2.log 2>&1
```

One process writes to a session at a time. An error saying the thread "already
has an active writer" means another `codex exec` or an interactive
`codex resume` still holds it.

When Computer Use reports that it "was not approved to use <App>", or a browser
call fails because "the permission request was dismissed", hand the approval to
the user:

1. Ask them to run `codex resume <session-id>`, send "try again", approve the
   prompt, and leave with `/exit`.
2. Continue with `codex exec … resume <session-id>`. The approval carries over.

## 5. Check the result

Open every screenshot, check that every file exists, and read `final.md` and
the end of `run.log`. Codex's summary describes what it meant to do; the files
show what happened. Report each blocker Codex wrote down.

## Guardrails

- Leave Codex's approval records (`~/.codex/browser/sessions/`,
  `~/.codex/computer-use/sessions/`, and the `com.openai.sky.CUAService`
  preferences) for the user's approval dialogs to write.
- Use `--approve-for-me`, never `--dangerously-bypass-approvals-and-sandbox`,
  which also removes Codex's command sandbox.
- Stop only Codex runs you started. Match a process to its run by working
  directory (`lsof -p <pid> | rg cwd`) before stopping it.
