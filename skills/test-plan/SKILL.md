---
name: test-plan
description: Use when asked to plan pre-production feature checks.
---

# Test plan

Plan the end-to-end checks that would make you confident shipping the feature
to prod, and ask the user for the access you lack. Plan only, in the chat; the
plan is throwaway.

1. List every behavior the change adds or alters and every contract it touches,
   from the diff, the PR, and its Linear issue or spec. Include APIs, schemas,
   stored data, flags, events, and callers and callees in other services.
2. List the ways each change could fail in prod: old and new code running side
   by side on the same data, migrations and rollback, real data volume and
   shape, retries and partial failure, concurrency, tenant and permission
   boundaries, and config that differs by environment. Skip what unit and
   integration tests in CI already catch.
3. Probe each place a check could run with one cheap read-only call: the local
   app, each environment's Grafana MCP, databases through
   `catalog-guided-db-access`, the browser through `computer-use`, flag and
   deploy tooling, test accounts, and third-party sandboxes. Unprobed access
   counts as missing.
4. For every risk you won't accept, plan an end-to-end check, as the user-level
   Testing rules describe, that would go red if the risk happened, covering
   every code path the change adds. Give where it runs, the exact command or
   steps, and what passes. When a check compares against a baseline, such as a
   metric, a row count, or a response, say what to capture before the deploy
   and what to compare after it.
5. Add the prod signals to watch after deploy and the reading that triggers a
   rollback.

Mark every check that writes to QA or staging. Before running one, have the
user confirm that the environment it points at, by host, is non-production.

Show the services and components the checks drive, and the path each check
takes through them, in a Mermaid diagram. Keep the rest short: each check in a
line or two, marked runnable or blocked, then the risks you'd accept unchecked
with a reason each, and for each missing access the tool, environment, and
scope to grant and the checks it unblocks. Ask whether to run the runnable
checks.
