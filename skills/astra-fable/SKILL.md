---
name: astra-fable
description: Use when told 'fable judge'.
---

# Astra and Fable

Astra advises and Fable decides.

1. Start Astra on `gpt-6.2-astra` and Fable on `claude-fable-5-2` in
   parallel, each with a new `delegate_task`. Give both the same task: the
   question, what it's about, and where to look. Leave out your take and the
   user's lean. Ask for what the user wants back, with evidence and no score
   or verdict. Dropping the work is a valid answer.
2. Start a fresh Fable with the task and both answers verbatim. It decides
   which points hold, scores the work if the user asked for scores, and makes
   the call.
3. Report Fable's call and what it took from Astra.
4. When the user asks to iterate, make the changes Fable calls for and run
   the round again, until Fable has nothing left to change.
