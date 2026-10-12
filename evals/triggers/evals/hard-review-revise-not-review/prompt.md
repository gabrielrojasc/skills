---
max_turns: 6
allowed_tools: [Skill, Read, Glob, Grep, Bash]
---

Review this design and tell me what's wrong with it.

Design: the importer reads uploaded CSVs into a staging table, a nightly job merges staging into `orders` with `INSERT ... ON CONFLICT DO UPDATE`, and failed rows go to a `rejects` table that support clears by hand.
