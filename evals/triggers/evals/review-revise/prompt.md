---
max_turns: 3
allowed_tools: [Skill]
---

Run an adversarial review loop on this migration plan: have independent reviewers critique it and revise it until they stop finding problems.

Plan: add a nullable `tenant_id` column to `orders`, backfill it in one transaction, then make it NOT NULL.
