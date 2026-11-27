---
name: council
description: Use when the user explicitly writes 'council'.
---

# Council

Advisors gather evidence in parallel and a fresh judge makes the call. Use
`gpt-6.2-astra`, `claude-fable-5-2`, and `gemini-4-neon` as advisors, and a
fresh `claude-fable-5-2` as judge, unless the user overrides them.

## Round

1. Start all advisors in parallel, each with a new `delegate_task`. Give every
   advisor the same task: the question, what it's about, and where to look.
   Leave out your take and the user's lean. Ask for what the user wants back,
   with evidence and no score or verdict. Dropping the work is a valid answer.
   If an advisor fails or is unavailable, note it and continue with the
   answers that return. If the user marks an advisor non-blocking, cancel it
   and proceed once the blocking advisors finish.
2. Start a fresh judge with the task and every returned answer verbatim. The
   judge decides which points hold, notes any unique point that held from each
   advisor, scores the work when asked or given a rubric, and makes the call.
3. Report the judge's call, what it took from each advisor, and any advisor
   that failed.

## Iterate

When the user asks to iterate, score every round and repeat until the judge
has nothing left to change (unless a higher target was set), the stated target
is met, or the loop stalls.

- Use the user's rubric when given; otherwise have the judge state its criteria
  in round 1 on a 1-10 scale and keep those criteria fixed across all rounds.
- Treat the starting work as the baseline kept version. Make only the changes
  the judge calls for, fight scope creep, and run relevant checks before the
  next round.
- Keep a round only when its score improves, or clears a blocker with no
  criterion dropping, and no new blocker appears. Otherwise revert to the best
  kept version.
- Stop on a stall: two rounds in a row without improvement, the same issue
  repeating, or a call only the user can make, including the judge recommending
  to drop the work.
- When a round was reverted or a target was set, verify the kept version once
  with a fresh judge (task, criteria, and kept version only) so picking the
  best round doesn't inflate the final score.
- Report a round-by-round score table.
