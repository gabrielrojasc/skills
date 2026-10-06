---
name: gh-review-comments
description: Triages PR feedback. Use when reviewing unresolved comments.
---

# GitHub review comment triage

Decide how to handle the feedback on one or more PRs, get the user's approval,
then act on it. `<SKILL_DIR>` is this file's directory.

## 1. Fetch

Run `<SKILL_DIR>/scripts/fetch-pr-comments.py <pr>...`, or with no PR for the
current branch's. It returns unresolved inline threads, conversation comments,
and review bodies; add `--all-threads` or `--threads-only` only when asked. When
a thread's `comments.pageInfo.hasNextPage` is true, fetch the rest with
`gh api graphql`; if you can't, leave that item open and say so. Split comments
and review bodies into concrete concerns, merge duplicates while keeping every
source link, and treat praise and status summaries as context.

## 2. Classify

Read the cited code, diff, and tests first, using `gh pr diff` and `gh api`
when the checkout isn't the PR branch. With several PRs, give each its own
read-only subagent, all at once. Each item is:

- **Fix:** a real defect, missing behavior, contract mismatch, test gap, or
  maintainability problem worth changing. Nits count when the change genuinely
  improves the code.
- **Dismiss:** incorrect, stale, out of scope, or outweighed by an existing
  constraint.
- **Already addressed:** the code already handles it.

When a call hinges on product or preference, pick the best-supported one and
state the assumption.

## 3. Challenge each call

As each item is classified, start a background subagent that makes the
strongest evidence-backed case against the call: missed callers, contracts,
tests, or edge cases. Revise when it holds and send it back, until it returns
`No material objection` or a fresh progress agent finds the loop going in
circles. Your own review doesn't replace it. Mark any disagreement left as
`Disputed:` with the deciding assumption.

## 4. Decision pack

One block per item, numbered across PRs, so the user can decide without opening
a link:

```markdown
## PR <number>: <title>

Fix <n> · dismiss <n> · already addressed <n>

### 1 · Fix · P2

[path:line](link) · [thread](url)

**Concern:** what the reviewer says is wrong, in plain words.

**Assessment:** whether it holds and why.

**Plan:** the change and its scope.

**Reply:**

> the exact text, only when one is proposed

**Reaction:** 👍 or 👎, only for a bot comment
```

- Print file links with
  `<SKILL_DIR>/scripts/file-links.sh <owner>/<repo> <n> <path>:<line>...` and
  paste them unchanged.
- For each concern from a bot (`author.__typename` is `Bot`), propose 👍 when it
  was right and 👎 when it wasn't.
- Keep replies short and about the code.

End with one plain-text question, never a question tool: approve all, approve
by ID, or revise.

## 5. Act on approval

Change nothing before approval, and do only what was approved.

- Per PR, apply the fixes on one branch and run the covering checks once; work
  on separate PRs in parallel, each in its own worktree. Pushing keeps its own
  approval.
- Resolve a Fix or Already addressed thread once the fix is on the PR and checks
  pass, without waiting for CI. Leave partial or disputed threads open. Resolve
  a Dismiss thread only when the approval said so.
- Add approved reactions once each item is decided.
- Mutations: `addPullRequestReviewThreadReply` to reply in a thread,
  `resolveReviewThread` with the thread's `id`, `gh pr comment --body-file` for
  a top-level answer (a new comment that links its source), and `addReaction`.
  Pass bodies through a file.

Before ending, confirm each resolved thread's `isResolved`, and list any
approved thread left open with its reason.
