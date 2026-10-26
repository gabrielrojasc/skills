---
name: cross-review
description: Use when asked to cross-review and fix a change.
---

# Cross-review

Run `review-revise` on the change with the other agent as its one reviewer,
fix what holds up, and push. Don't ask the user. Commit locally each round.

The budget is 3 review rounds, or 5 when the change touches authentication,
authorization, secrets, deletion of stored data, or concurrency.

## Review

Start each round with a new `delegate_task` call to the other provider at the
chosen rung. Ask for a review of `<base>...HEAD` in the worktree's absolute
path against the change's intent, and add to the `review-revise` brief:

> Don't edit files. Skip style unless it hides a bug, and flag code, tests, or
> guards the intent doesn't need. Start each finding with a Conventional
> Comments label: `issue (blocking):` for a bug callers will hit in the
> intended behavior, security and data-loss risks included,
> `nitpick (non-blocking):` for anything else, or `question:`. Give each
> finding an ID, such as `F1`, and keep IDs across rounds. End with
> `VERDICT: APPROVE` or `VERDICT: CHANGES`.

Record the round's head and base SHAs, and answer the reviewer's questions
yourself.

## Fix

Adjudicate as `review-revise` says. A finding about another path, a rare case,
or a small cost is a nitpick whatever its label. Fix with the smallest change,
deleting or narrowing code before adding a lock, cache, helper, or option.
Decline a nitpick outside the change's purpose in one line and list it as a
follow-up. Run the checks and commit.

## Re-review

When this round changed behavior, beyond nitpicks and comment, doc, or format
changes, and the budget allows, start the next round. Pass the original brief,
every round's findings, the fixes, and the rejections with their reasons. Scope
it to the commits since the last review, their callers, and the open findings,
or to all of `<base>...HEAD` when the base SHA changed since that review.

## Finish

When the budget runs out with an `issue (blocking)` open, or the loop stalls as
`review-revise` defines it, stop without pushing and report what's unresolved;
running out of rounds isn't approval. Otherwise push.

Add this line to the PR description, or to your report when there is no PR:

```text
Cross-reviewed: <N> rounds with <model> on <head-sha> against <base-sha>. Verdict: <approved | changes requested | disputed: <ids> | incomplete>
```

The verdict is `approved` when the last round returned `VERDICT: APPROVE`, and
`disputed` when every open finding is one you rejected and the reviewer still
holds. It is `incomplete` when commits after the last reviewed one change
behavior, and `changes requested` otherwise. Report how many review rounds ran
with each round's `taskId`, the commits, and every rejection with its reason.
