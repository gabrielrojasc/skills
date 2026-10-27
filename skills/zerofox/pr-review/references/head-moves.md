# When the head moves

Start a folder for the new head, with its own `src/`, and carry forward the
finding IDs, drafts, and triage decisions. Don't restart triage.

1. If findings carried over, a fresh verifier checks each against the new head,
   as in Verify, and returns **still applies** (re-anchored to its new line),
   **fixed** (with the commit that fixed it), or **changed** (still real, with
   a revised draft).
2. In parallel, run
   `<SKILL_DIR>/scripts/changes-since-review.py <owner>/<repo> <n> <old-head>`
   and review what it reports as in Setup. New findings go through Verify.
3. Keep the user's earlier decision on findings that still apply. Drop fixed
   ones. Raise or route changed, new, and untriaged findings as in Triage, with
   a one-line list of what carried over or was fixed.
4. Rebuild the review and follow Submit, marking which comments carried over
   unchanged.

If the head moves again, repeat against the latest head.
