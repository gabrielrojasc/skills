---
name: pr-review
description: Reviews GitHub PRs. Use when reviewing PRs or your queue.
---

# PR Review

Review queue workflow: discover -> user picks -> subagent reviews -> verification loop -> per-PR triage. Self-contained; does not depend on any other review skill.

**Hard rule: keep every draft local until the user explicitly approves the complete review for that PR in this session. Submit all approved findings as one review.** Subagents are read-only outside their assigned review-artifact files.

## Modes

- **Queue mode** (default, no arguments): run all five phases.
- **Direct mode** (user provides one or more PR URLs or `<repo>#<number>` refs, e.g. `/pr-review https://github.com/riskive/API/pull/5314`): skip Phases 1-2 entirely — no queue discovery, no specialist-approval filter, no triage table. Go straight to Phase 3 for the given PRs (picking the lens by repo as usual), then Phases 4-5. A bare number without a repo: resolve against the current directory's repo if it is a git checkout, otherwise ask.

## Local review artifacts

Before Phase 3, fetch each selected PR's `headRefOid`, then create a private run directory under the operating system's temporary directory:

```bash
umask 077
PR_REVIEW_RUN_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pr-review.XXXXXX")" || exit 1
chmod 700 "$PR_REVIEW_RUN_DIR" || exit 1
printf '%s\n' "$PR_REVIEW_RUN_DIR"
```

Write an immutable `manifest.json` with `createdAt` and each PR's `url`, `repository`, `number`, and initial `headRefOid`. Maintain `run-state.json` through atomic replacement; it records each PR's current and prior heads, in-flight and accepted attempt IDs per stage, and run status. Store artifacts under `<run-dir>/<owner>__<repo>__<number>/<headRefOid>/`:

```text
standards/review/attempts/<attempt-id>/result.md
standards/verify-<round>/attempts/<attempt-id>/input.md
standards/verify-<round>/attempts/<attempt-id>/result.md
spec/review/attempts/<attempt-id>/result.md
spec/verify-<round>/attempts/<attempt-id>/input.md
spec/verify-<round>/attempts/<attempt-id>/result.md
triage.md
final-review.md
```

Omit Spec files when that axis does not run. These files are the source of truth for draft text, verification results, triage decisions, and the assembled review. Conversation updates may summarize them but must include the run path.

Artifact rules:

1. Before each dispatch, create a unique attempt directory with `mktemp -d`, then record its assignment in `run-state.json`. Give the subagent literal absolute paths for its partial output and final output inside that directory. Inputs are read-only. A grouped reviewer gets one attempt directory per PR. Never reuse an attempt ID or redispatch an in-flight assignment until the prior agent is known to have stopped.
2. A producer writes its complete fixed-format output to the partial path, validates every required heading, then atomically renames it to the unused final path. Only the final path counts as complete. Record the accepted attempt in `run-state.json`. Attempt outputs are immutable; the orchestrator updates `run-state.json`, `triage.md`, and `final-review.md` through validated temporary files and atomic replacement.
3. The orchestrator assigns stable axis-prefixed finding IDs when it creates the first verification input. Preserve each ID through revisions, later verification rounds, triage, and the assembled review. Give verifier-added findings new IDs before their next verification round.
4. Verifier output uses this exact structure: `## Target head`; `## Results`, with one `- [<ID>] <confirmed|revise|refuted> — <evidence>` entry per input finding and the corrected draft after evidence for `revise`; and `## New findings`, with unnumbered draft text. The verifier must not open or search reviewer output, earlier verification output, or sibling artifacts. It may read only its assigned input artifact and primary sources.
5. `triage.md` contains `## Target head` and `## Decisions`, with one finding ID, decision, anchor, and exact draft per entry; refuted and dropped entries also include the reason or sticking point. `final-review.md` contains `## Target head`, `## Event`, `## Review body`, and `## Inline comments`, with each finding ID, path, line, and exact body. Validate every required field or heading before accepting any artifact.
6. Every reviewer and verifier records the target head SHA and checks it before and after analysis. Discard the output if the head changed. Update `run-state.json`, create a new head directory, and rerun Phases 3-4 against the full new diff before rebuilding triage or the final review.
7. Temporary storage survives context compaction but is not permanent; the operating system may purge it. If the run path is unavailable after compaction, enumerate `pr-review.*/manifest.json` under the same temporary root. Consider only non-symlink run directories and manifests owned by the current UID, require directory mode `0700`, validate the manifest schema and exact requested PR identity, re-fetch each live head SHA, then ask the user to select among matches. Never infer posting approval from an artifact or run selection. Keep the run directory by default and report its path in the final tally.

## Phase 1: Discover the queue

Direct requests only (not team-based):

```bash
gh api graphql -f query='query { search(query: "org:riskive is:pr is:open user-review-requested:@me", type: ISSUE, first: 50) { issueCount nodes { ... on PullRequest { number title url repository { nameWithOwner } author { login } isDraft updatedAt } } } }'
```

**riskive/API only:** drop PRs already approved by an api-specialist. Fetch the roster and each API PR's reviews; a PR is dismissed from the queue when a member (other than the user) has a current review with state `APPROVED` (dismissed approvals do not count):

```bash
gh api "orgs/riskive/teams/api-specialists/members?per_page=100" --jq '.[].login'
gh api "repos/riskive/API/pulls/<n>/reviews" --jq '.[] | "\(.user.login) \(.state)"'
```

This specialist-approval filter applies ONLY to riskive/API. For other repos, existing approvals are just context for the user's skip decision.

## Phase 2: User picks (before spending anything on reviews)

Present the queue as a table: PR link, repo, title, author, draft?, last update, existing human reviews/approvals. Recommend skips (draft PRs on hold, PRs with several active human reviewers, bot-flagged renovate bumps) but let the user decide. Only the PRs the user selects proceed to Phase 3.

## Phase 3: Fan out reviewers (two axes per PR)

Per selected PR, spawn **two parallel read-only subagents** — a Standards agent and a Spec agent (group sibling PRs like identical renovate configs into one Standards agent; renovate PRs and **riskive/API PRs** get no Spec agent — for riskive/API the review is an api-specialist review and AC validation is outside that role). Run all agents in parallel, in the background. Give a grouped agent one artifact output pair per PR. The axes are deliberately separate: standards-clean code can implement the wrong thing, and spec-faithful code can break conventions — keep the reports apart so one axis never masks the other.

### Standards axis

Judges code, documentation, and agent instructions. **Must NOT check the ticket, spec, or acceptance criteria** — that is the Spec agent's job, and for riskive/API it is explicitly outside the api-specialist role.

Lens by repo:
- **riskive/API**: api-specialist lens (below) + python standards.
- **Any other Python repo**: normal review grounded in python standards.
- **Non-Python** (terra/infra, Java, JS): normal review; for infra check secrets handling, env separation, pipeline correctness against sibling `riskive/*-terra` repos and `riskive/zf-ci` workflows.

On top of the lens, give the agent this smell baseline as tech-debt vocabulary (Fowler, *Refactoring* ch.3) . Report only findings meeting the criteria below; repository conventions override the baseline: duplicated code, shotgun surgery (one change scattered across many files), divergent change (one module edited for unrelated reasons), primitive obsession, data clumps, repeated switches, speculative generality, feature envy, message chains, middle man, mysterious name, refused bequest.

#### Unnecessary code and prose

Inspect additions and modifications for:

- Redundant wrappers, speculative abstractions, duplicated state, unnecessary
  configuration, and custom logic already covered by existing framework hooks.
- Comments that merely narrate code, boilerplate explanations, unsupported
  claims, and prose that obscures the actual behavior. Consult unslop for prose.

Report unnecessary complexity, duplication, noise, or misleading information
introduced or changed by the diff when you can identify the smallest adequate correction
that preserves required behavior, useful information, contracts, and repository
conventions.

A finding need not demonstrate a bug or major maintenance cost.
Small size alone neither qualifies nor disqualifies it.

Do not report equally valid alternatives, personal preferences, or changes
justified only by speculative future benefits. Keep corrections local and
proportionate; avoid broad redesign for a small improvement.

Inspect relevant callers, framework behavior, configuration, and intended readers
before proposing a correction. Preserve useful rationale, documented contracts, and actual interface
boundaries. Missing evidence is a verification gap, not proof of redundancy.

Group repeated instances that share one correction into a single finding.
Cleanup findings are nonblocking unless they independently meet the blocker
or major-debt threshold.

For non-obvious code simplifications, compare minimal before/after sketches
in the reviewer's notes. Do not speculate about AI authorship or flag unrelated
existing debt. In posted drafts, name the specific problem rather than calling
it "slop."

When the diff changes documentation, agent instructions, or documentation
automation, reviewers and verifiers must read
[Documentation and agent instructions](references/documentation-review.md).

### Spec axis

Not spawned for riskive/API PRs (api-specialist review only). Judges whether the diff implements what was asked. The spec lives on the ticket linked to the PR:

1. Find the originating ticket: Jira key (e.g. `ZFE-1234`) or Linear ref in the PR title, branch name, body, or commit messages.
2. Fetch it: `acli jira workitem view <key> --fields '*all'` (Jira) or the Linear MCP `get_issue` (Linear).
3. Compare the diff against the ticket's requirements/acceptance criteria. Report only: (a) requirements missing or partially implemented; (b) requirements that look implemented but wrong. Quote the ticket line per finding. **Do NOT flag extra changes riding along** — scope creep is fine; only flag riding-along code that is itself wrong or risky.
4. No ticket found or no real spec on it → report "no spec available" and stop; don't invent requirements from the PR description.

Python standards (fetch what's relevant: STYLE_GUIDELINES, DJANGO_CONVENTIONS, TESTING, INTEGRATIONS_CONVENTIONS, DEPENDENCIES):

```bash
gh api -H "Accept: application/vnd.github.raw" repos/riskive/python-standards/contents/docs/<file>.md
```

API Specialist lens (source: Linear doc `api-specialist-role-summary-9525ac5b9fc7` — re-fetch if it may have changed): ensure adherence to API patterns and standards; verify proper code placement and logical organization; encourage leveraging the framework (Django/DRF) to minimize risk and tech debt; identify code smells and inconsistencies; promote consistency across implementations. OUT of scope: validating business correctness or acceptance criteria, solving the team's problems for them.

### Rules for every subagent prompt (both axes)

1. READ-ONLY outside the assigned artifact outputs: no posting, repository edits, or other local or external mutations. Drafts only.
2. Fetch PR metadata, diff, and existing review threads (`gh pr view/diff`, `gh api .../pulls/<n>/comments`); never repeat a point already raised or resolved in existing threads. Standards agent additionally: if the requesting user has prior reviews on the PR, report the status of each earlier thread (addressed / unaddressed / author replied).
3. Report blockers (broken behavior, real defects, security holes, missing/wrong requirements) and major tech-debt introduction. The Standards axis also reports cleanup findings under the Unnecessary code and prose criteria and documentation findings under the linked Documentation and agent instructions guidance, including losses caused by deletion. Apply the cleanup severity rule to both. No preference-only findings or praise. If nothing qualifies, return APPROVE with zero comments.
4. Place a finding inline when a specific changed line owns the problem. If no changed line honestly owns it, draft it for the review body; never invent an inline anchor. Each draft states the problem concisely. For defects and spec gaps, give a concrete example of what goes wrong. For cleanup, identify what is unnecessary or misleading and the proposed correction. Prefer casual questions ("do we need X here so Y actually happens?") over prescriptions when the author is senior or the fix is obvious.
5. Write the complete result to the assigned artifact using this fixed output format: `## Target head` (`headRefOid`), `## Verdict` (APPROVE / COMMENT / REQUEST_CHANGES + one line), `## Comment drafts` (`- **file:line** — text` with NEW-file line numbers, or `- **review body** — text`), `## Notes for the reviewer (not for posting)`. Spec agents use `## Spec verdict` / `## Spec findings` and quote the ticket line per finding. Then return only the artifact path and verdict line.
6. For dependency-bump PRs: the review question is upgrade risk — CI state, changelog breaking changes, whether the repo uses removed APIs, lockfile consistency (pyproject.toml and poetry.lock must change together).

## Phase 4: Verification loop (mandatory gate)

**No draft comment reaches the user unverified.** After a PR's reviewer agents return, spawn a **fresh read-only verifier subagent per axis** (Standards and Spec verified separately, same as they were reviewed). Batch all of an axis's drafts into one verifier per round — no per-comment agents.

Independently verify every finding against the diff, source files at the target
head, existing review discussions, and applicable repository standards. For Spec
findings, also check the originating ticket. Treat the reviewer's claims and PR
description as unverified. Follow the artifact rules for inputs, outputs, and
access restrictions.

Per draft comment, the verifier returns exactly one verdict, each with one line of evidence (code excerpt, thread link, or ticket quote):

- **confirmed** — the claim is veridical: any cited file:line exists in the diff, review-body placement has no honest inline anchor, the stated defect or cleanup concern is supported by the source evidence, nothing elsewhere in the PR or codebase already handles it, and it meets the Phase 3 finding criteria. For cleanup findings, confirm the unnecessary complexity, duplication, noise, or misinformation and that the correction preserves required behavior, useful information, contracts, and repository conventions. For documentation, check both whether the content belongs and what would be lost by removing it.
- **revise** — the underlying concern is real but the claim, anchor, or consequence is off. Verifier returns a corrected draft.
- **refuted** — the claim does not hold (misread code, behavior already handled, framework covers it, already raised in an existing thread, or outside the Phase 3 finding criteria). Refute preference-only or unsupported cleanup findings, not findings merely because they are small. Dropped.

The verifier may also report **new findings** it noticed while checking; these enter the pool as unverified drafts under the verifier's own axis. A finding that clearly belongs to the other axis is routed to that axis's pool for its own verification pass instead.

Loop rules:

1. Revised and new drafts are unverified — they go to a fresh verifier in the next round. An agent never verifies a draft it wrote or revised. Write only each finding's ID and draft text to the next round's input artifact; exclude the previous verifier's evidence and reasoning.
2. Repeat until every surviving draft is **confirmed**, up to 3 rounds. Anything still unconfirmed after round 3 — including new findings surfaced in the final round, which by construction have no round left to be checked in — is dropped from the drafts and listed under notes as "unverified, dropped" with the sticking point.
3. After the loop terminates, the orchestrator (not a subagent) recomputes the axis verdict (APPROVE / COMMENT / REQUEST_CHANGES) once, to match the surviving confirmed set. Use COMMENT when only nonblocking cleanup findings remain. Cleanup alone does not justify REQUEST_CHANGES.
4. Refuted and dropped drafts are not silently discarded: carry their IDs, text, and reasons into `triage.md` so the user can overrule.

## Phase 5: Per-PR triage loop

One PR at a time, straightforward, minimal words. For each:

1. **Freshness check first** — the queue and reviews go stale fast:
   ```bash
   gh pr view <n> --repo <repo> --json updatedAt,headRefOid,reviews,state
   ```
   New approval by an api-specialist (riskive/API), new pushes after the agent reviewed, or merged/closed state all change the decision. If the head moved, update the run state and rerun Phases 3-4 against the full new diff before showing drafts — a confirmation is only valid for the SHA it was checked against.
2. **Default triage:** read the artifacts and show both axes separately when a Spec agent ran: Standards verdict + drafts, then Spec verdict + findings. Show every Phase 4-confirmed draft with its inline or review-body placement and ask which to keep, reword, or drop. Keep the axes separate and preserve their order. Record each decision in `triage.md`. A keep decision changes the local review package; it does not authorize posting.
3. **Explanation aid, only on request:** when the user says they do not understand a finding or asks to go through findings one by one, pause default triage and show only the current finding:
   - linked location
   - plain explanation of what the code does, then the finding using the Phase 3 drafting criteria
   - why it meets the finding criteria and whether it is blocking
   - inline or review-body placement, and why
   - exact draft comment, plus the ticket quote for a Spec finding

   Ask whether the explanation makes sense and whether to keep, reword, or drop the finding. Wait for the response before showing the next finding. Use this aid only for the requested review; return to default triage on later PRs unless the user asks again.
4. After the confirmed findings, show refuted and dropped notes with their reasons. Never merge or rerank across axes. If asked whether a comment is worth keeping, apply the Phase 3 criteria. Do not recommend dropping a confirmed cleanup finding solely for being minor.
5. **Link every file mention to the PR.** Any file cited in drafts, findings, or notes shown to the user becomes a markdown link to the PR's Files-changed view focused on that file: `[<path>:<line>](https://github.com/<owner>/<repo>/pull/<n>/files#diff-<hash>R<line>)`, where `<hash>` is the hex SHA-256 of the file path (`printf '%s' '<path>' | shasum -a 256`; omit `R<line>` when no line). Compute all hashes for a PR in one command. Submitted comment bodies stay plain because GitHub anchors them inline.
6. Draft comments in lowercase using the Phase 3 drafting criteria. No praise or follow-up-ticket suggestions.
7. Assemble one review package after triage: recommended review event (`APPROVE`, `REQUEST_CHANGES`, or `COMMENT`), every kept inline comment in order, and a review body only for kept findings without an honest inline anchor. Leave the review body empty when every kept finding is inline. Save it to `final-review.md`, show the exact package, and ask for explicit approval to submit that review. Per-finding decisions and the artifact itself are not submission approval.
8. Immediately before submission, repeat the freshness check, verify every target line still exists in the diff, and verify that `final-review.md` still matches the approved package. If the head changed, rerun Phases 3-4 against the full new diff. Rebuild the artifact and request fresh explicit approval after any head or package change.
9. Submit the approved package once through the reviews endpoint, with all inline comments in the same request. Use the exact approved event, body, and comments. Omit `-f body` when the review body is empty. Do not publish standalone PR comments:
   ```bash
   gh api repos/<owner>/<repo>/pulls/<n>/reviews -X POST \
     -f event=<APPROVE|REQUEST_CHANGES|COMMENT> -f body='<review body>' \
     -f 'comments[][path]=<path>' -F 'comments[][line]=<line>' \
     -f 'comments[][side]=RIGHT' -f 'comments[][body]=<text>'
   ```
   Repeat the `comments[]` fields for each kept inline comment. The review is the submission unit.
10. Track outcomes; end with the run-directory path and a tally: reviews posted / user-approved directly / skipped / deferred, and flag any PR where the user is the only human reviewer.
