---
name: babysit-pr
description: Drives PRs to merge-ready. Use when babysitting a PR.
disable-model-invocation: true
---

# Babysit PR

Fix review feedback and CI failures in rounds, without asking the user, until
each PR is ready for them to take over. Watch every PR's checks yourself, and
give each round a fresh subagent that runs steps 2 to 5 and returns raised items
instead of asking; ask the user and pass the answers to that PR's next round. A
stack runs as one loop, bottom up.

1. Wait in the background for the head's checks to settle with
   `gh pr checks <pr> --watch`, once the new head's checks have appeared.
2. Handle the feedback with `gh-review-comments`.
3. Fix each failed check, flaky tests and failures already on the base branch
   included. Those fixes count as within the PR's scope; add each one beyond its
   purpose to the PR description, keeping the rest of it. Rerun a transient
   failure once, and raise it if it repeats. Raise a fix that changes a contract
   or rests on an assumption, as `gh-review-comments` defines them.
4. When the PR conflicts with its base, rebase onto it. Raise a conflict whose
   resolution needs judgment.
5. Push once, with the CI and feedback fixes together.

Stop when required checks pass, no unresolved thread is left except ones the
user kept open, and nothing conflicts. Hand the PR over with its link, what
changed across rounds, fixes beyond its purpose, and what's left for the user,
such as approvals, reviewers, draft state, and merging. If a fresh progress
agent finds the rounds going in circles, stop and report what's unresolved and
what each round tried.
