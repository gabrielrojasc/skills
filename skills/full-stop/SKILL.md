---
name: full-stop
description: Use when told 'full stop'.
---

# Full stop

The user said "full stop" because they won't watch this thread. This skill
runs unattended: own the work from its current state to a PR the user can
merge, and leave the merge to them. When the user only mentions the phrase,
for example asking what it means, work normally instead.

`<SKILL_DIR>` is this file's directory. Before step 1, check that
`<SKILL_DIR>/../cross-review/SKILL.md`, `<SKILL_DIR>/../babysit-pr/SKILL.md`,
and `<SKILL_DIR>/../pr/SKILL.md` exist, and report any that is missing
instead of starting. Also confirm the Linear issue for the `ref:` footer the
user-level Git rules require, and ask now if there is none.

1. Finish the change the user agreed to, and commit it.
2. Prove it with the end-to-end check the user-level Testing rules ask for,
   and keep its artifact. If nothing you can run proves the change, ask.
3. Review it with `cross-review`. If it stops without pushing, hand off as
   Blocked with its report.
4. If `gh pr list --head <branch>` shows no PR, file one with the `pr` skill.
   Open its Summary with one sentence on the problem, in the user's words. Add
   how you proved the change and the `cross-review` verdict line.
5. Run `babysit-pr` until it reports an end state.
6. When babysitting changed behavior after the last proof or review and
   `cross-review`'s budget has a round left, prove it again, run
   `babysit-pr`'s step 2 check, run one more `cross-review` round scoped by its
   step 4, update the verdict line, and return to step 5. When the budget is
   spent, set the verdict to `incomplete` and hand off.

Ask only when you can't prove the change, the goal is ambiguous in a way that
changes the result, or the next step is a one-way door. Decide the rest
yourself. Merging, enabling auto-merge, and adding the PR to a merge queue
stay with the user.

Hand off with `babysit-pr`'s end state, or Blocked when the run stopped before
step 5, plus the PR link, head and base SHAs, the proof and its artifact, the
verdict line, the follow-ups, and each decision you made for the user.
