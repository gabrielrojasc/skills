# Slack follow-ups

Give a subagent the Slack connector and a start date. It finds asks made to me
and promises I made, in DMs, mentions, and threads I took part in, and checks
each against later replies, PRs, and tickets. It returns the open ones in a
table: who, the ask, its due date, and a link.

If the connector fails, report that it couldn't read Slack, so I don't read an
empty table as nothing owed. Name every search that hit its result limit.

Merge the table into the update's single reply.
