---
name: babysit-pr
description: Drives PRs to merge-ready. Use when babysitting a PR.
disable-model-invocation: true
---

# Babysit PR

Fix review feedback and CI failures in rounds, without asking the user, until
each PR is ready for them to take over. A stack runs as one loop, bottom up.

1. Call `watch_pull_request` on each PR. Run the first round right away, then
   end your turn after each round until a wake starts the next. On a wake,
   wait in the background until every check that isn't gated finishes. A
   gated check belongs to a workflow run that waits on maintainer approval,
   which `gh run list --commit <head-sha> --status action_required` or
   `--status waiting` lists. Leave gated checks to the user; they are neither
   pending nor failed.
2. Give each round a fresh subagent that runs steps 3 to 6 and returns raised
   items as `gh-review-comments` decision-pack blocks instead of asking. To ask
   the user, unwatch every PR, watch again once they answer, and pass the
   answers to that PR's next round.
3. Handle the feedback with `gh-review-comments`.
4. Fix each failed check, flaky tests and failures already on the base branch
   included. Those fixes count as within the PR's scope; add each one beyond its
   purpose to the PR description, keeping the rest of it. Rerun a transient
   failure once, and raise it if it repeats. Raise a fix that changes a contract
   or rests on an assumption, as `gh-review-comments` defines them.
5. When the PR conflicts with its base, rebase onto it. Raise a conflict whose
   resolution needs judgment.
6. Push once, with the CI and feedback fixes together.

Stop when required checks pass or are gated, no unresolved thread is left except
ones the user kept open, and nothing conflicts. Unwatch every PR before you hand
it over or stop. Hand the PR over with its link, what changed across rounds,
fixes beyond its purpose, and what's left for the user, such as approvals, gated
runs, reviewers, draft state, and merging. If a fresh progress agent finds the
rounds going in circles, stop and report what's unresolved and what each round
tried.
