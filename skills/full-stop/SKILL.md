---
name: full-stop
description: Use when told 'full stop'.
---

# Full stop

The user said "full stop" because they won't watch this thread. This skill
runs unattended: own the work from its current state to a PR that Fable calls
ready to merge and deploy after weighing Astra's review. When the user only
mentions the phrase, for example asking what it means, work normally instead.

Before step 1, confirm the Linear issue for the `ref:` footer the user-level
Git rules require, and ask now if there is none.

1. Finish the change the user agreed to, and commit it.
2. Prove it with the end-to-end check the user-level Testing rules ask for,
   and keep its artifact. Open no one-way door for the proof. If nothing you
   can run without one proves the change, ask.
3. Review it with `cross-review`, and leave its push to step 4. If it stops
   with findings open, hand off as Blocked with its report.
4. If `gh pr list --head <branch>` shows a PR, run `babysit-pr`'s merge-queue
   check. Push, and if there was no PR, file one with the `pr` skill. Open its
   Summary with one sentence on the problem, in the user's words. Add how you
   proved the change and the `cross-review` verdict line.
5. Run `babysit-pr` until it reports an end state. Hand off if it's Blocked.
6. Prove the change again if the last proof failed or behavior changed after
   it. On failure, go to step 8.
7. Unless Fable said `READY` on the current head in this run, start two new
   `delegate_task` calls in parallel at the `consequential` rung's effort,
   Astra on `gpt-6.2-astra` and Fable on `claude-fable-5-2`. Ask each whether
   the PR is ready to merge and deploy, apart from pending approvals. Leave
   deploy out only when the repository ships nothing deployable, such as a
   docs-only repository. Give each the PR, the proof, every review round's
   findings, fixes, and rejections, and `cross-review`'s Review brief. When
   Astra finishes or fails, send the result to Fable's thread with
   `t3_thread_send`. Fable decides which findings hold and ends with `READY`,
   or with `NOT READY` naming each blocker or missing evidence. Add its
   verdict to the PR description with the head and base SHAs it reviewed.
8. Unless Fable says `READY` on the current head and `babysit-pr`'s end state
   still holds, run `babysit-pr`'s merge-queue check, fix or gather the
   missing evidence as `cross-review`'s Fix section says, push any commits,
   and return to step 5. Hand off as Blocked when the loop stalls as
   `review-revise` defines it.

Ask only when you can't prove the change, the goal is ambiguous in a way that
changes the result, or the next step is a one-way door. Decide the rest
yourself. Merging, enabling auto-merge, and adding the PR to a merge queue
stay with the user.

Hand off with `babysit-pr`'s end state, or Blocked when step 3 or 8 stopped
the run, plus the PR link, head and base SHAs, the proof and its artifact, the
verdict line, Fable's verdict, the follow-ups, and each decision you made for
the user.
