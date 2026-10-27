---
name: gh-review-comments
description: Use when addressing PR review feedback.
---

# GitHub review comment triage

Classify feedback on one or more PRs, fix what holds up, and reply to every
thread. Raise only what needs the user's judgment. A skill that runs this one
may take over the push and the question; follow its brief. `<SKILL_DIR>` is
this file's directory.

## Fetch

Run `<SKILL_DIR>/scripts/fetch-pr-comments.py <pr>...`, or with no PR for the
current branch's. It returns unresolved inline threads, conversation comments,
and review bodies; add `--all-threads` or `--threads-only` only when asked.
Split comments and review bodies into concrete concerns, merge duplicates while
keeping every source link, and treat praise and status summaries as context.

## Classify

Read each PR's code in a local worktree on its branch, or fetch its head with
`<SKILL_DIR>/scripts/fetch-source.sh <owner>/<repo> <head-sha> <dir>` into a
`mktemp -d` directory. With several PRs, give each its own read-only subagent,
all at once. Each item is:

- **Fix:** a real defect, missing behavior, contract mismatch, test gap, or
  maintainability problem worth changing. Nits count when the change genuinely
  improves the code and stays within the PR's purpose.
- **Dismiss:** incorrect, stale, out of scope, or outweighed by an existing
  constraint. List a valid nit beyond the PR's purpose as a follow-up in your
  report.
- **Already addressed:** the code already handles it.

When the code can't settle a call, as with product behavior, preference,
ownership, or the author's intent, check the PR body, its linked issue, and the
conversation, and cite what settles it. Otherwise pick the best-supported call
and state the assumption.

## Check the dismissals

Once a PR's items are classified, start one read-only subagent for that PR
that makes the strongest evidence-backed case against each Dismiss and Already
addressed call, by number. Flip a call to Fix when its objection holds. Mark a
call `Disputed:` with the deciding assumption when you reject an objection.
Skip this check when the PR has no such calls.

## Raise

Raise an item for the user's judgment when any of these holds; every other item
is routine:

- It rests on an assumption: it is `Disputed:` or nothing cited settles it.
- It does work beyond the PR's purpose.
- It dismisses or only partly accepts a human's comment, other than a nit
  listed as a follow-up.

Give each raised item its link from
`<SKILL_DIR>/scripts/file-links.sh <owner>/<repo> <n> <path>:<line>...`, pasted
unchanged, the concern, your pick and why, and the exact change or reply, so
the user can decide without opening the link. Ask about raised items in one
question, and start on routine items without waiting for the answer.

## Fix

Routine items carry the user's standing approval; raised items need their
answer. Do nothing beyond the two. Commit the fixes, then push each PR once,
after all its items are settled, so bots re-review once.

## Reply

Once the fixes are pushed, reply, react, and resolve Fix, Already addressed,
and routine Dismiss threads, without waiting for CI. React to every comment you
answer with `THUMBS_UP` or `THUMBS_DOWN` for whether it was right.

- Resolve a thread only once its reply mutation returned the comment's `url`.
  Leave partial or disputed threads open, and resolve a raised Dismiss only
  when the user said so.
- Mutations: `addPullRequestReviewThreadReply` to reply in a thread,
  `resolveReviewThread` with the thread's `id` from the fetch output,
  `gh pr comment --body-file` for a top-level answer (a new comment that links
  its source), and `addReaction`. Pass bodies through a file.

Before ending, fetch again with `--threads-only` and without `--all-threads`.
No thread you resolved may appear in it; list each thread left open with its
reason.
