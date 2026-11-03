---
name: open-items
description: Use when asked broadly what's open, pending, or on your plate.
---

# Open items

When the ask names a specific item or topic, answer about that item only and skip the list.
When asked what's next, give only the next step.

1. Read `/home/box/t3-tots/unsettled-threads.json` and keep only the entries whose `owner` is you.
2. Read the open Linear issues assigned to Gabriel in your lane, as your description defines it.
3. Match issues to threads by their links, so each item shows up once.
4. Reply in three groups, in this order, and skip any group that's empty:
   - **Waiting on you**: entries with status waiting-on-gabriel. Write each as a short question or the exact action.
   - **Moving**: running, pr-open and waiting-on-others.
   - **Parked**: kept-open, idle, and Linear issues with no thread. Collapse the group to one line: the count, plus any item that needs Gabriel, and offer "show parked" for the full list.
   Give each item one line: a short plain name, a link to its Linear issue if it has one, and a link to each of its PRs next to it. After the links, write only the status or next step in a few words. Write no bare ticket IDs.
5. Only read: change nothing, and don't nudge anyone.
