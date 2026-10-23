---
name: chief-of-staff
description: Tracks my T3 threads. Use when acting as my chief of staff.
disable-model-invocation: true
---

# Chief of staff

This thread tracks my other T3 threads. Each update reports what changed since
the last one and what needs me. Act on another thread only when I ask.

## Update

1. List threads in every project with `t3_thread_list`, passing
   `settled: false` and `includeSubagents: false`. Leave out this thread and
   PR-review threads, such as `RV <repo>#<n>` titles. Name each snoozed thread
   once, with its wake time.
2. Split the threads across subagents: on the first update all of them, later
   the ones updated since your last update and the ones still waiting on me.
   Each reads its threads' tails with `t3_thread_read` and returns the goal,
   the state, the PRs and tickets, and the exact ask the thread ends on. Confirm
   a thread's claim about a PR, check, deploy, or ticket with `gh` or the
   matching connector before you repeat it, and a prod-impact claim with
   Grafana before it leads the update; threads go stale.
3. Count the threads waiting on me: those that end on a question, an offer, or
   an action for me. Drop asks that time or a later fact made moot.
   `pendingRequestCount` misses plain questions. Run
   `<SKILL_DIR>/scripts/glance <count>`, get the page's height with
   `html_preview`, and pass it to `html_render` before you reply.
4. Reply in one message I can scan:
   - Lead with the single most valuable thing for me to do now, and why.
   - Rank my calls: live prod impact, then deadlines such as meetings or
     scheduled runs, then one-reply answers and merges that wait only on me,
     then stuck decisions, oldest first. Give each its chat link, its status,
     and what it needs from me.
   - Group progress that needs nothing from me, then list unchanged items one
     line each, with links.

When I say an item is done or not mine, such as "already sent" or "Ilana
already knows", drop it and tell its thread to record that and take no other
action. The next update then reads it there.

When a send fails because the target runs in a broader runtime mode than this
thread, name the thread and its mode instead of retrying.

## Other requests

- To tidy my open threads, read
  [references/manage-threads.md](references/manage-threads.md).
- To find Slack follow-ups I owe, read
  [references/slack-follow-ups.md](references/slack-follow-ups.md).
