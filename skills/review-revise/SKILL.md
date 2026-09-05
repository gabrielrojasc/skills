---
name: review-revise
description: Reviews and revises. Use when adversarial loops are requested.
---

# Review-revise

Run a bounded adversarial review of code, prose, plans, or recommendations.
Use when invoked by name or when the user explicitly asks for an adversarial
review-revise loop. Ordinary review or implementation requests do not trigger it.

## Workflow

1. Establish the target, requirements, evidence, and authorized edits from the
   current task. A review-only request permits revising the assessment or proposed
   patch, not changing the underlying artifact. Preserve the task's approval gates.
   Default to one reviewer and at most three review rounds. Honor explicit counts
   and budgets. State these defaults briefly before dispatch.

2. Dispatch independent, read-only subagents. Give each the target or exact
   revision, requirements, constraints, relevant source locations, and one bounded
   review assignment. With multiple reviewers, assign distinct concerns that
   together cover the target. Let them inspect source evidence independently of
   the author's rationale. Choose each model and reasoning effort explicitly
   using the active agent-selection policy. Reviewers must not edit, publish,
   or delegate further. If delegation is unavailable, report the limitation;
   self-review does not satisfy this workflow.

   Use this brief, adapted to the assignment:

   > Find material reasons this work fails its requirements. Check assumptions,
   > edge cases, and unnecessary complexity against source evidence. Return each
   > objection with its location, consequence, evidence or counterexample, and
   > smallest adequate correction. Separate unresolved evidence gaps from
   > demonstrated defects. Report `No material objection` if none remain. Finding
   > a problem is not a quota; preference alone is not a defect.

3. Adjudicate every objection against the evidence. Merge duplicates. Accept and
   fix supported findings within scope; reject unsupported findings with a
   concrete reason. Keep a compact record in the conversation of each finding,
   disposition, and verification. Resolve disagreements through source checks or
   bounded experiments, not reviewer votes. If resolution requires missing
   authority or a human decision, finish independent work and report the blocker.

4. Run the checks appropriate to each accepted revision. Send the revised target,
   changes, verification results, and any rejection rationale back to the relevant
   reviewers. Ask them to verify dispositions and inspect for regressions. Any
   reviewer whose assignment is affected must review the latest revision. Count
   each review-and-response cycle as one round; parallel reviewers share a round.

5. Stop when all assigned reviewers return `No material objection` for the current
   target and required checks pass. Otherwise repeat within the budget. Stop early
   when a round produces no progress on unresolved objections. At the round limit,
   report remaining objections and any changes still awaiting review. A budget
   limit, unavailable reviewer, or unresolved disagreement is not a clean result.

## Report

Summarize the changes, checks, reviewer count, rounds used, and remaining
objections or unverified changes. Keep the report proportional to the work.
