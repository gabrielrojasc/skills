---
name: cross-review
description: Use when asked to cross-review and fix a change.
---

# Cross-review

Have the other agent review the change, fix what holds up, and ask it for a
re-review until nothing is left to fix or the round budget runs out. Don't ask
the user. Commit locally each round.

The budget is 3 review rounds, or 5 when the change touches authentication,
authorization, secrets, deletion of stored data, or concurrency.

1. Call `delegate_task` with the other provider at the chosen rung. Ask for a
   review of `<base>...HEAD` in the worktree's absolute path against the
   change's intent, and tell the reviewer not to edit files. Have it start each
   finding with a Conventional Comments label: `issue (blocking):` for a
   defect, security and data-loss risks included, `nitpick (non-blocking):` for
   mechanical cleanup, or `question:`. Have it end with `VERDICT: APPROVE` or
   `VERDICT: CHANGES`. Record the round's head and base SHAs. Answer the
   reviewer's questions yourself.
2. Classify and challenge the findings with steps 2 and 3 of the
   `gh-review-comments` skill, treating the change as one PR.
3. Make the fixes, run the checks, and commit.
4. When this round fixed anything beyond nitpicks and comment, doc, or format
   changes, and the budget allows, ask for a re-review with a new
   `delegate_task` call. Pass the original brief, every round's findings, the
   fixes, and the dismissals with their reasons. Scope it to the commits since
   the last review, their callers, and the open findings, or to all of
   `<base>...HEAD` when the base SHA changed since that review. Repeat from
   step 2.

When the budget runs out with an `issue (blocking)` open, or the loop goes in
circles, stop without pushing and report what's unresolved; running out of
rounds isn't approval. Otherwise push.

Add this line to the PR description, or to your report when there is no PR:

```text
Cross-reviewed: <N> rounds with <model> on <head-sha> against <base-sha>. Verdict: <approved | changes requested | disputed: <ids> | incomplete>
```

The verdict is `approved` when the last round returned `VERDICT: APPROVE`, and
`disputed` when its open findings are all `Disputed:` dismissals. It is
`incomplete` when commits after the last reviewed one change behavior, and
`changes requested` otherwise. Report how many review rounds ran with each
round's `taskId`, the commits, and every dismissal with its reason.
