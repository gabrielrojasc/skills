# When the head moves

Start a folder for the new head, with its own `src/`, and carry forward the
finding IDs, drafts, and any triage decisions. Don't restart triage.

1. A fresh verifier checks every carried finding against the new head, with the
   same inputs and limits as in Verify. Each gets one verdict: **still applies**
   (re-anchored to its new line), **fixed** (name the commit that resolved it),
   or **changed** (still real, but the claim, anchor, or draft needs a revision,
   which the verifier supplies).
2. In parallel with step 1, run
   `<SKILL_DIR>/scripts/changes-since-review.py <owner>/<repo> <n> <old-head>`.
   On `changed`, a reviewer per axis reviews only the printed differences, as
   in Check for an earlier review, and its drafts go through Verify as usual.
   On `same`, as after a plain rebase, there is nothing new to review. On
   `unknown`, it reviews the full diff.
3. Findings that still apply keep the user's earlier decision, and the user
   isn't asked about them again. Fixed findings are dropped. Show one message
   with what needs a decision (changed findings, new findings, and findings not
   yet triaged, in the triage format) and a one-line list of what carried over
   or was fixed, then ask one question. If nothing needs a decision, say so and
   go straight to the package.
4. Rebuild the package and ask for approval, marking which comments carried over
   unchanged.

If the head moves again, repeat against the latest head.
