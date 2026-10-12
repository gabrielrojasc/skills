---
max_turns: 6
allowed_tools: [Skill, Read, Glob, Grep, Bash]
---

I don't trust my own read on this design. Get it torn apart by fresh eyes a few times and fold in what holds up.

Design: the importer reads uploaded CSVs into a staging table, a nightly job merges staging into `orders` with `INSERT ... ON CONFLICT DO UPDATE`, and failed rows go to a `rejects` table that support clears by hand.
