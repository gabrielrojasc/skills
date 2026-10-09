---
name: gh-review-comments
description: Triages PR review comments. Use when addressing PR feedback.
---

# GitHub review comment triage

Classify feedback on one or more PRs, raise only what needs the user's
judgment, and handle the rest without asking. `<SKILL_DIR>` is this file's directory.

## 1. Fetch

Run `<SKILL_DIR>/scripts/fetch-pr-comments.py <pr>...`, or with no PR for the
current branch's. It returns unresolved inline threads, conversation comments,
and review bodies; add `--all-threads` or `--threads-only` only when asked. When
a thread's `comments.pageInfo.hasNextPage` is true, fetch the rest with
`gh api graphql`; if you can't, leave that item open and say so. Split comments
and review bodies into concrete concerns, merge duplicates while keeping every
source link, and treat praise and status summaries as context.

## 2. Classify

Read each PR's code in a local worktree on its branch, or fetch its head with
`<SKILL_DIR>/scripts/fetch-source.sh <owner>/<repo> <head-sha> <dir>` into a
`mktemp -d` directory. With several PRs, give each its own read-only subagent,
all at once. Each item is:

- **Fix:** a real defect, missing behavior, contract mismatch, test gap, or
  maintainability problem worth changing. Nits count when the change genuinely
  improves the code.
- **Dismiss:** incorrect, stale, out of scope, or outweighed by an existing
  constraint.
- **Already addressed:** the code already handles it.

When the code can't settle a call, as with product behavior, preference,
ownership, or the author's intent, check the PR body, its linked issue, and the
conversation, and cite what settles it. Otherwise pick the best-supported call
and state the assumption.

## 3. Challenge each call

As each item is classified, start a background subagent that makes the
strongest evidence-backed case against the call: missed callers, contracts,
tests, or edge cases. Revise when it holds and send it back, until it returns
`No material objection` or a fresh progress agent finds the loop going in
circles. Your own review doesn't replace it. Mark any disagreement left as
`Disputed:` with the deciding assumption.

## 4. Decision pack

Raise an item for the user's judgment when any of these holds; every other item
is routine:

- It rests on an assumption: it is `Disputed:` or nothing cited settles it.
- It changes a contract or scope: user-visible behavior, a public API, config,
  stored data, a dependency, or work beyond the PR's purpose.
- It dismisses or only partly accepts a human's comment.

Give each raised item a full block so the user can decide without opening a
link, then list routine items one line each. Number items across PRs:

```markdown
## PR <number>: <title>

### 1 · Fix

[path:line](link) · [thread](url)

**Concern:** what the reviewer says is wrong, in plain words.

**Assessment:** whether it holds and why.

**Decide:** what the user must settle, and your pick.

**Plan:** the change and its scope.

**Reply:**

> the exact text, only when one is proposed

**Reaction:** 👍 or 👎, only for a bot comment

### Routine

| # | Call | Item | Action |
| - | ---- | ---- | ------ |
| 2 | Fix | [path:line](link) · [thread](url) | the change, reply, and reaction |
```

- Print file links with
  `<SKILL_DIR>/scripts/file-links.sh <owner>/<repo> <n> <path>:<line>...` and
  paste them unchanged.
- For each concern from a bot (`author.__typename` is `Bot`), propose 👍 when it
  was right and 👎 when it wasn't.
- Keep replies short and about the code.

Ask about raised items in one plain-text question, never a question tool, and
start on routine items without waiting for the answer.

## 5. Act

Routine items carry the user's standing approval; raised items need their
answer. Do nothing beyond the two.

- Per PR, apply the fixes on one branch and run the covering checks once; work
  on separate PRs in parallel, each in its own worktree.
- Push each PR once, after all its items are settled, so bots re-review once.
- Then reply, react, and resolve Fix, Already addressed, and routine Dismiss
  threads, without waiting for CI. Leave partial or disputed threads open, and
  resolve a raised Dismiss only when the user said so.
- Mutations: `addPullRequestReviewThreadReply` to reply in a thread,
  `resolveReviewThread` with the thread's `id`, `gh pr comment --body-file` for
  a top-level answer (a new comment that links its source), and `addReaction`.
  Pass bodies through a file.

Before ending, confirm each resolved thread's `isResolved`, and list any
thread left open with its reason.
