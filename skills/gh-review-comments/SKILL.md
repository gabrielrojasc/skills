---
name: gh-review-comments
description: Triages PR feedback. Use when reviewing unresolved comments.
disable-model-invocation: true
---

# GitHub review comment triage

Resolve `<SKILL_DIR>` as the directory containing this `SKILL.md` before running the bundled helper.

## Overview

Fetch review feedback from one or more GitHub pull requests, inspect the relevant code or diff, and propose how to handle each unresolved item. The default output is a review-comment proposal the human can approve, revise, or reject.

Use this skill when the user asks to:

- fetch unresolved comments from one PR or multiple PRs
- assess PR review comments
- decide whether comments should be fixed or dismissed
- draft the proposal before applying fixes or posting replies

## Workflow

1. Identify the PRs.
   - Accept explicit PR URLs, PR numbers, `#123`, or `owner/repo#123`.
   - If no PR is provided, use the PR associated with the current branch.
   - For multiple PRs, keep the findings grouped by PR.
2. Fetch comments.
   - Run `<SKILL_DIR>/scripts/fetch-pr-comments.py <pr> [<pr> ...]` for unresolved inline review threads.
   - Unresolved review threads are the default.
   - Use `--all-threads` only when the user asks to inspect resolved threads too.
   - Use `--include-context` only when top-level PR conversation comments or review bodies are needed. They can be noisy because bot summaries often include large generated reports.
   - Treat top-level PR conversation comments and review bodies as context only. Do not turn review-summary text, bot summaries, or non-threadable nitpicks into reply targets.
3. Inspect the relevant code.
   - Read the cited files, diff hunks, tests, and nearby code before judging a comment.
   - If the local checkout is not the PR branch, prefer `gh pr diff <pr>` and read-only `gh api` lookups over changing branches.
   - Do not make code changes, post comments, resolve threads, or change PR state during assessment.
4. Classify each actionable item.
   - An actionable item is an unresolved review thread returned under `review_threads`.
   - **Fix**: the comment identifies a real defect, missing behavior, contract mismatch, test gap, or maintainability problem worth changing.
   - **Dismiss with reply**: the comment is incorrect, stale, out of scope, or outweighed by existing constraints.
   - **Already addressed**: the diff or code already handles it; propose a short confirming reply only if useful.
   - Every item must get one of these recommendations. If a comment depends on product, ownership, rollout, or style preference, choose the best recommendation from the evidence and make the assumption explicit in the proposal.
5. Have independent subagents adversarially review every preliminary recommendation.
   - For each actionable item, dispatch an independent judgment-tier subagent with the review comment, relevant code and diff evidence, preliminary classification, assessment, and proposed action. The subagent reviews only and makes no changes.
   - The primary agent may revise recommendations, but only the assigned subagent's verdict satisfies this review gate. Never replace or waive the delegated review with primary-agent self-review.
   - Ask it to make the strongest evidence-backed case that the recommendation is wrong, identify missed callers, contracts, tests, or edge cases, and propose a better recommendation when needed.
   - Check each critique against the source evidence and revise the recommendation when the critique holds.
   - Send the revised recommendation back to its assigned subagent. Continue the delegated review-revise loop until the subagent returns `No material objection` or further resolution requires evidence or a human choice outside the current scope.
   - If a material disagreement remains, state it and the deciding assumption in the decision pack. Do not present disputed judgment as settled fact.
6. Produce a compact decision pack and ask for approval.
   - Ask one concise chat approval question after the decision pack.
   - Do not edit code or reply on GitHub until the human approves the proposal or a subset of items.

## Decision pack format

Keep the proposal compact enough to make a decision without becoming a wall of text. Prefer numbered blocks over tables. Do not force a rigid template when a shorter recommendation is clearer.

Start with a compact rollup:

- `Fix: <count>`
- `Dismiss: <count>`
- `Already addressed: <count>`

Then list each unresolved item as a compact numbered block. Every block must include the finding, severity, assessment, and proposed action. Include the thread URL when it is useful for traceability or when proposing a reply.

```markdown
## PR <number>: <title>

Verdict: Fix <count>, dismiss <count>, already addressed <count>.

#: <item-number>
<reviewer> finding: <path>:<line> - <short concern>
Thread: <review-thread comment URL>
Severity: <P0 | P1 | P2 | P3 | Nit>
Assessment: <short evidence-backed judgment, usually 2-5 sentences>
Proposed action: <Fix | Dismiss with thread reply | Already addressed>. <concrete plan or reply rationale>
Draft thread reply: <only for Dismiss with thread reply or Already addressed>
────────────────────────────────────────
```

For **Fix** items, omit `Draft thread reply` unless the user asked for fix-response text too. If extra evidence is needed, add one short `Evidence:` line rather than expanding the block into a mini-report. Keep replies concise and scoped to the reviewed code. Do not mention private chat context as evidence.

Separate items with `────────────────────────────────────────` so each recommendation is visually distinct without expanding into a larger template.

After the decision pack, ask one concise approval question in chat. The user can approve all, approve specific item numbers, skip items, or ask for revisions.

## Approval rules

- The proposal is read-only.
- Fixes require explicit human approval.
- For approved fixes, implement only the approved scope. Before committing,
  trace the changed behavior through affected callers and consumers. Test the
  reported defect and any relevant edge or failure paths, then run the smallest
  suite that covers them.
- Dismissal replies require explicit human approval and must target a review thread.
- Resolving review threads requires explicit human approval separate from posting a reply unless the user already asked to resolve them.
- If the human approves only some items, handle only those items.

## Posting replies after approval

Use the least broad mutation needed:

- Inline review thread reply: `gh api graphql` with `addPullRequestReviewThreadReply`.
- Resolve a thread only when approved: `gh api graphql` with `resolveReviewThread`.
- Top-level PR comments are out of the default flow. Use `gh pr comment <pr> --body-file <file>` only when the user explicitly asks to post a top-level PR comment, and never as a substitute response for review-summary text or non-threadable nitpicks.

Prefer writing reply bodies to a temporary file and passing `--body-file` or `-F body=@<file>` so shell quoting cannot corrupt the message.

## Rules

- Ground every recommendation in code, diff, test, or PR evidence.
- Do not repeat prior reviewer text as the agent's own assessment.
- Do not pad the proposal with low-confidence findings.
- Push back on weak review comments when evidence shows they are wrong.
- Preserve read-only boundaries until the human approves implementation or replies.
- For multiple PRs, avoid cross-contaminating evidence between PRs unless the same code path is explicitly shared.
- Do not respond top-level on the PR to review-summary nitpicks, bot rollups, or comments that do not have a review thread. If a concern has no threadable comment, mention it as context only.
