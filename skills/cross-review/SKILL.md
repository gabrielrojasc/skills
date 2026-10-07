---
name: cross-review
description: Cross-model review loop. Use when the other agent should review.
disable-model-invocation: true
---

# Cross-review

Have the other agent review the change, fix what holds up, and ask it for a
re-review until nothing is left to fix. Don't ask the user. Commit locally each
round and push once nothing is left to fix.

1. Ask the other agent for a review on `<base>...HEAD` with the skill the user
   named. Otherwise use `pr-review` when it's installed, and `code-review` when
   not. From Claude Code, run Codex as one unchained command, in the background:

   ```bash
   codex exec --approve-for-me --skip-git-repo-check -C <repo> -o <out>.md "<prompt>" < /dev/null > <out>.log 2>&1
   ```

   From Codex, run Claude outside the sandbox:

   ```bash
   claude -p "<prompt>" --permission-mode auto --output-format json < /dev/null > <out>.json
   ```

2. A fresh subagent, without your reasoning, triages the findings with the
   /gh-review-comments skill. It decides instead of asking the user, and there
   are no PR threads to reply to or resolve.
3. Make the fixes, run the checks, and commit.
4. Ask the same reviewer session for a re-review, passing the fixes and the
   dismissals with their reasons (`codex exec … resume <id>` or
   `claude -p --resume <id>`). Repeat from step 2.

When a round leaves nothing to fix, push. If the loop goes in circles, stop
without pushing and report what's unresolved. Report the commits and every
dismissal with its reason.
