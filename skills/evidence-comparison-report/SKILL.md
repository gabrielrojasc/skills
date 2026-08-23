---
name: evidence-comparison-report
description: Use when creating a reusable evidence-backed comparison.
---

# Evidence comparison report

Produce a comparison artifact that another person can inspect, update, or use for a decision. Use ordinary chat or research for lookups, single-subject assessments, and comparisons that do not require a persistent artifact.

## Preflight

Before research begins, establish:

- The alternatives, candidate universe, or benchmark objective.
- The intended reader and downstream use.
- The material decision criteria and hard exclusions.
- An absolute output path inside a user-approved writable workspace.

The current request must explicitly authorize a persistent artifact. Prior context may inform the report, but it does not authorize a filesystem write. If the request does not establish an output destination, propose one and get approval before writing.

## Workflow

1. Bound the candidate universe.
   - Start with user-provided candidates.
   - Name authoritative discovery sources and the stopping rule.
   - Label an unbounded result as a sampled shortlist.
2. Define evaluation criteria before ranking.
   - State what evidence supports each criterion.
   - Use weights only when the evidence supports that precision.
3. Research the unresolved dimensions.
   - Prefer primary sources, then independent testing and real-world evidence.
   - Use the installed `$research` skill when reading legwork should run in a background agent and its repo-local research file is within the approved artifact scope.
   - A research task may name several repositories. Split it only when independent questions benefit from separate agents.
4. Reconcile claims.
   - Record strong supporting evidence, contradictions, currentness, and confidence.
   - Separate observed facts from preference fit.
5. Write the report at the approved path.
   - Lead with the recommendation or benchmark result.
   - Expose scope, criteria, exclusions, uncertainty, and sources.
   - Create intermediate notes only when they materially improve auditability.
6. Verify the artifact.
   - Check candidate names, conclusions, source links, and time-sensitive claims.
   - Parse or render the chosen format before finishing.

Read [report-guidelines.md](references/report-guidelines.md) when choosing evidence strength, handling bias, or structuring the final report.

## Completion criteria

- The report exists at the approved absolute path.
- Candidate scope and coverage limits are explicit.
- Evaluation criteria are visible before the conclusions they support.
- Major claims have inspectable sources and contradictory evidence is addressed.
- Conclusions match the evidence without fake precision.
- The final format has been parsed or rendered successfully.
