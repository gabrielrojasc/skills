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
   - Run `<SKILL_DIR>/scripts/fetch-pr-comments.py <pr> [<pr> ...]` for unresolved inline review threads, top-level PR conversation comments, and review bodies by default.
   - Use `--all-threads` only when the user asks to inspect resolved threads too.
   - Use `--threads-only` only when the user limits triage to inline threads.
   - Inspect each thread's `comments.pageInfo`. If `hasNextPage` is true, fetch remaining comments with `gh api graphql` using the thread ID and `endCursor`, continuing until complete. Missing pagination metadata also means completeness is unknown. If full history cannot be obtained, report the evidence gap instead of finalizing that item's triage and leave the thread open.
   - Extract concrete concerns from `conversation_comments` and `reviews`, including bot summaries. Top-level feedback has no thread-resolution status; check whether the current code or later discussion addresses it.
   - Merge duplicate concerns across sources, retaining their source URLs. Treat status reports, praise, and summaries without concrete concerns as context.
3. Inspect the relevant code.
   - Read the cited files, diff hunks, tests, and nearby code before judging a comment.
   - If the local checkout is not the PR branch, prefer `gh pr diff <pr>` and read-only `gh api` lookups over changing branches.
   - Do not make code changes, post comments, resolve threads, or change PR state during assessment.
4. Classify each actionable item.
   - An actionable item is an unresolved review thread or a distinct concrete concern from a top-level comment or review body. Split independent concerns in one body into separate items.
   - **Fix**: the comment identifies a real defect, missing behavior, contract mismatch, test gap, or maintainability problem worth changing.
   - **Dismiss**: the comment is incorrect, stale, out of scope, or outweighed by existing constraints. Propose a reply only when useful.
   - **Already addressed**: the diff or code already handles it; propose a short confirming reply only if useful.
   - Every item must get one of these recommendations. If a comment depends on product, ownership, rollout, or style preference, choose the best recommendation from the evidence and make the assumption explicit in the proposal.
5. Have independent subagents adversarially review every preliminary recommendation.
   - Dispatch independent reviewers for every actionable item. Related items may share a reviewer; require a separate verdict for each item. Choose each reviewer's model and effort using the active agent-selection policy. Provide the comments, relevant code and diff evidence, classifications, assessments, and proposed actions. Reviewers make no changes.
   - The primary agent may revise recommendations, but only the assigned subagent's verdict satisfies this review gate. Never replace or waive the delegated review with primary-agent self-review.
   - Ask it to make the strongest evidence-backed case that the recommendation is wrong, identify missed callers, contracts, tests, or edge cases, and propose a better recommendation when needed.
   - Check each critique against the source evidence and revise the recommendation when the critique holds.
   - Send the revised recommendation back to its assigned subagent. Continue the delegated review-revise loop until the subagent returns `No material objection` or further resolution requires evidence or a human choice outside the current scope.
   - If a material disagreement remains, state it and the deciding assumption in the decision pack. Do not present disputed judgment as settled fact.
6. Produce a compact decision pack and ask for approval.
   - Ask one concise chat approval question after the decision pack.
   - Do not edit code or reply on GitHub until the human approves the proposal or a subset of items.
7. Complete approved actions and resolve addressed inline threads.
   - For **Fix** and **Already addressed** items, verify that the current PR contains the correction and relevant checks pass before resolving. A local-only fix is not sufficient; preserve existing push approval gates.
   - Check that every concern in the thread is addressed. Leave partially addressed, disputed, or blocked threads open.
   - Resolve eligible threads with `resolveReviewThread`, confirm the returned `isResolved` state, and report any failures or threads left open.

## Decision pack format

Keep the proposal compact enough to make a decision without becoming a wall of text. Prefer numbered blocks over tables. Do not force a rigid template when a shorter recommendation is clearer.

Start with a compact rollup:

- `Fix: <count>`
- `Dismiss: <count>`
- `Already addressed: <count>`

Then list each unresolved item as a compact numbered block. Every block must include the finding, severity, assessment, and proposed action. Include the source URL for traceability and identify whether it is an inline thread, conversation comment, or review body. For inline threads, include the intended resolution in the proposed action.

```markdown
## PR <number>: <title>

Verdict: Fix <count>, dismiss <count>, already addressed <count>.

#: <item-number>
<reviewer> finding: <location, if applicable> - <short concern>
Source: <source type and URL>
Severity: <P0 | P1 | P2 | P3 | Nit>
Assessment: <short evidence-backed judgment, usually 2-5 sentences>
Proposed action: <Fix | Dismiss | Already addressed>. <concrete plan or reply rationale>
Draft reply: <if useful for Dismiss or Already addressed; state the destination>
────────────────────────────────────────
```

For **Fix** items, omit `Draft reply` unless the user asked for fix-response text too. If extra evidence is needed, add one short `Evidence:` line rather than expanding the block into a mini-report. Keep replies concise and scoped to the reviewed code. Do not mention private chat context as evidence.

Separate items with `────────────────────────────────────────` so each recommendation is visually distinct without expanding into a larger template.

After the decision pack, ask one concise approval question in chat. The user can approve all, approve specific item numbers, skip items, or ask for revisions.

## Approval rules

- The proposal is read-only.
- Fixes require explicit human approval.
- For approved fixes, implement only the approved scope. Before committing,
  trace the changed behavior through affected callers and consumers. Test the
  reported defect and any relevant edge or failure paths, then run the smallest
  suite that covers them.
- Replies require explicit human approval of their text and destination. Top-level feedback does not authorize posting or resolving a review thread.
- Approval to address a **Fix** or **Already addressed** inline item includes resolving its thread after verification, unless the user asks to leave it open. No second approval is needed. Approval to post a reply alone does not authorize resolution.
- For **Dismiss** items, resolve only when the approved proposal explicitly includes resolution.
- If the human approves only some items, handle only those items.

## Posting replies and resolving threads after approval

Use the least broad mutation needed:

- Inline review thread reply: `gh api graphql` with `addPullRequestReviewThreadReply`.
- Resolve an eligible addressed thread: `gh api graphql` with `resolveReviewThread`, using the review thread's `id`, not a comment or review ID. Top-level comments and review bodies have no resolvable thread state.
- For an approved response to a conversation comment or review body, use `gh pr comment <pr> --body-file <file>` and link the original source. This creates a new top-level comment; it does not reply to or resolve an inline thread.

Prefer writing reply bodies to a temporary file and passing `--body-file` or `-F body=@<file>` so shell quoting cannot corrupt the message.

## Rules

- Ground every recommendation in code, diff, test, or PR evidence.
- Do not repeat prior reviewer text as the agent's own assessment.
- Do not pad the proposal with low-confidence findings.
- Push back on weak review comments when evidence shows they are wrong.
- Preserve read-only boundaries until the human approves implementation or replies.
- For multiple PRs, avoid cross-contaminating evidence between PRs unless the same code path is explicitly shared.
- Judge concrete concerns by evidence, regardless of whether they came from an inline thread, a person, or a bot summary.

## Verify the fetcher

Run the offline regression checks after changing the helper:

```bash
python3 -B <SKILL_DIR>/tests/test-fetch-pr-comments.py
```
