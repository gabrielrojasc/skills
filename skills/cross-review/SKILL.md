---
name: cross-review
description: Cross-model review loop. Use when the other agent should review.
disable-model-invocation: true
---

# Cross-review

Have the other agent review the change, fix what holds up, and ask it for a
re-review until nothing is left to fix. Don't ask the user. Commit locally each
round and push once nothing is left to fix.

1. Call `delegate_task` with the other provider at the chosen rung. Ask for a
   review of `<base>...HEAD` in the worktree's absolute path with `pr-review`
   when it's installed and `code-review` when not, and tell the reviewer not to
   edit files. Answer the reviewer's questions yourself.
2. Classify and challenge the findings with steps 2 and 3 of the
   `gh-review-comments` skill, treating the change as one PR.
3. Make the fixes, run the checks, and commit.
4. Ask for a re-review with a new `delegate_task` call. Pass the original
   brief, every round's findings, the fixes, and the dismissals with their
   reasons. Repeat from step 2.

When a round leaves nothing to fix, push. If the loop goes in circles, stop
without pushing and report what's unresolved. Report how many review rounds
ran with each round's `taskId`, the commits, and every dismissal with its
reason.
