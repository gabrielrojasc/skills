---
name: my-plate
description: Use when asked what's on your plate or the status of your items.
---

# My plate

1. Read `/home/box/t3-tots/unsettled-threads.json` and keep only the entries whose `owner` is you.
2. Read the open Linear issues assigned to Gabriel in your lane, as your description defines it.
3. Match issues to threads by their links, so each item shows up once.
4. Reply in three groups, in this order, and skip any group that's empty:
   - **Waiting on you**: entries with status waiting-on-gabriel, each with the exact decision.
   - **Moving**: running, pr-open and waiting-on-others.
   - **Parked**: kept-open, idle, and Linear issues with no thread.
   Use one line per item, with the item named and linked and its status in plain words.
5. Only read: change nothing, and don't nudge anyone.
