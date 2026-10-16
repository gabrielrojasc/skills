---
name: cross-review
description: Cross-model review loop. Use when the other agent should review.
disable-model-invocation: true
---

# Cross-review

Have the other agent review the change, fix what holds up, and ask it for a
re-review until nothing is left to fix. Don't ask the user. Commit locally each
round and push once nothing is left to fix.

1. Call `delegate_task` with the other provider at the chosen rung and a new
   `clientRequestId`. Ask for a review of `<base>...HEAD` with `pr-review` when
   it's installed and `code-review` when not, and tell the reviewer not to edit
   files. End the turn until the result wakes you. Answer the reviewer's
   questions yourself with `t3_pending_request_respond`.
2. A fresh subagent, without your reasoning, loads the `gh-review-comments`
   skill and triages the findings with it. It decides instead of asking the
   user, and there are no PR threads to reply to or resolve.
3. Make the fixes, run the checks, and commit.
4. Ask for a re-review with a new `delegate_task` call. Pass the original
   brief, every round's findings, the fixes, and the dismissals with their
   reasons. Repeat from step 2.

When a round leaves nothing to fix, push. If the loop goes in circles, stop
without pushing and report what's unresolved. Report the commits and every
dismissal with its reason.
