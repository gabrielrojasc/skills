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
   - Any other bot: use the check in the T3 Tots message that started this
     turn, which lists open items, says it found none, or says it couldn't
     read the thread. If that message has no check, or none started this
     turn, ask T3 Tots to run `anything-open-or-settle` on the thread, and
     wait for its reply.
2. Count as open whatever the thread leaves without an answer or a ticket:
   - a request, question, or decision from Gabriel or a reviewer;
   - a follow-up or promise, such as a check on a later date;
   - an error, a failed run or check, or a flake with no known cause;
   - work it says is unproven, paused, or not live yet;
   - an open linked PR, or a branch, worktree, or temporary resource it left;
   - anything it asks Gabriel to consider.
3. Raise the open items first, one line each with its link, even past a bot's
   nudge limit. T3 Tots gives them, or that it checked and found none, or that
   it couldn't read the thread, to whoever asked, Gabriel or a bot, or else to
   the thread's owning bot with the settle question. In a turn Gabriel didn't
   start, it messages him about nothing.
4. Then ask whether to settle the thread, keep it open, or file follow-ups
   first, with your pick. Pick keep open when an open item is work the thread
   was asked to finish. With nothing open, say you checked, then ask. If T3 Tots
   couldn't read the thread, the bot that got its message tells Gabriel so and
   holds the question.
