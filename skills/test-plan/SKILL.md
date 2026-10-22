---
name: test-plan
description: Plans pre-prod checks. Use when a feature is ready to ship.
disable-model-invocation: true
---

# Test plan

Plan the checks that would make you confident shipping the feature to prod,
find out which ones you can run with your current access, and ask the user for
the access the rest need. Plan only; run nothing that changes state.

1. Pin down the feature from the diff against its base, the PR, and the linked
   Linear issue or spec. Done when you can list every behavior the change adds
   or alters and every contract it touches: APIs, schemas, stored data,
   config, flags, permissions, events, and other services that call it or that
   it calls.
2. List the risks, the ways each change could fail in prod. Include data
   written by old and new code side by side, migrations and their rollback,
   real data volume and shape, partial failure and retries, concurrency,
   tenant and permission boundaries, config that differs between
   environments, and what a rollback leaves behind. Read the tests that cover
   the changed code and mark each risk they already catch.
3. Probe your access. For each place a check could run, make one cheap
   read-only call and record whether it worked: the test suite, running the
   app locally, CI, each environment's logs and metrics through its Grafana
   MCP, databases through `catalog-guided-db-access`, the signed-in browser
   through `computer-use`, flag and deploy tooling, test accounts, and
   third-party sandboxes. An access you didn't probe counts as missing.
4. Write a check for every risk not already caught. Each check names the risk,
   where it runs (local, CI, QA, staging, or prod after deploy), the exact
   command or steps, and the result that passes. A check must go red if its
   risk happens. Prefer driving the real system along the user's path over
   isolated tests. Add the prod signals to watch after deploy and the reading
   that should trigger a rollback.
5. Mark each check runnable now or blocked, with the access it's missing. A
   check that writes to a shared environment is runnable only after the user
   approves it.

Reply with the plan as a table of risk, check, where, and status, then the
risks you'd accept without a check and why. End with the access requests, one
per missing access: what it is, which blocked checks it unlocks, and the
weaker check you'd fall back to without it. Ask whether to run the runnable
checks.
