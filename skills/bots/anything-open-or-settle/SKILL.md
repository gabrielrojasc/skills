---
name: anything-open-or-settle
description: Use when `anything-open-or-settle` is explicitly written.
---

# Anything open or settle

Check the thread before any settle question. A done signal, such as a merged
PR or a closed issue, says one piece finished, not that nothing is left.

1. Get the thread's open items.
   - T3 Tots: read the thread on its computer with
     `t3 thread show <thread id> --json --messages 40`, plus its ledger entry's
     `followUp`.
   - Any other bot: ask T3 Tots for the open items and wait for its reply.
2. Count as open whatever the thread leaves without an answer or a ticket:
   - a request, question, or decision from Gabriel or a reviewer;
   - a follow-up or promise, such as a check on a later date;
   - an error, a failed run or check, or a flake with no known cause;
   - work it says is unproven, paused, or not live yet;
   - an open linked PR, or a branch, worktree, or temporary resource it left;
   - anything it asks Gabriel to consider.
3. Raise the open items first, one line each with its link, even past a bot's
   nudge limit. T3 Tots hands them to the thread's owning bot with the settle
   question, and messages Gabriel about nothing.
4. Then ask whether to settle the thread, keep it open, or file follow-ups
   first, with your pick. Pick keep open when an open item is work the thread
   was asked to finish. With nothing open, say you checked, then ask. If T3 Tots
   can't read the thread, say so and hold the question.
