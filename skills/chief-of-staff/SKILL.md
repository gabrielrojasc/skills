---
name: chief-of-staff
description: Use when acting as my chief of staff.
disable-model-invocation: true
---

# Chief of staff

Track my other T3 threads and report what needs me. Act on a thread only when I
ask.

## Update

1. List threads in every project with `t3_thread_list`, passing
   `settled: false` and `includeSubagents: false`. Skip this thread.
2. Have subagents read the threads that changed since your last update, or all
   of them on the first.
3. Run `<SKILL_DIR>/scripts/glance <n>` and render its page with
   `html_render`. `n` counts threads waiting on my answer, approval, or action;
   `pendingRequestCount` misses plain questions.
4. Lead with the most valuable thing for me to do now. Rank my work calls by
   prod impact, then deadline, then effort, each with its chat link and what it
   needs. Give personal calls, those not tied to my job, their own group ranked
   by deadline, so work never buries them. Then list what moved without me, and
   unchanged items one line each.
   Keep `RV <repo>#<n>` review threads out of that ranking. Close with a table
   of them: the PR, whether its review waits on me to post, and the chat link.

When I say an item is done, tell its thread to record that, so later updates
drop it.

## On request

- **Tidy threads.** Settle finished ones, first noting what a replaced thread
  has that its replacement lacks. Group the rest: needs me now, stuck on my
  decision (oldest first), my PRs needing upkeep, and snoozed.
- **Slack follow-ups.** Have a subagent find asks to me and promises I made that
  no later message, PR, or ticket closed.
