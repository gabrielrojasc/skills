# References

Sources that shaped these skills, with what each contributed and the skills
it touched.

## Agent and review design

- [When to fold subagents into your main agent loop](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop)
  (Anthropic). Default to one agent loop with skills. Keep a subagent only for
  parallel work that needs a fresh context, independent verification, or a
  context the main loop would bloat. Shaped the subagent rule in `AGENTS.md`,
  the dismissal check in `gh-review-comments`, and the readers in
  `chief-of-staff`.
- [Solving code review at Anthropic](https://claude.dev/blog/solving-code-review-at-anthropic/)
  (Anthropic). Parallel bug hunters, a separate group that votes on each
  finding, and filters that drop style and cleanup findings. After three
  rounds the reviewer asks the author to rethink the approach, since about 59%
  of what later rounds found predated the PR. Shaped the 3-round default in
  `review-revise` and the finding bar in `pr-review`.
- [How to Build an AI Code Review Agent](https://youtu.be/4UtrRVtUN_g) (Daksh
  Gupta, Greptile). Nitpicks wreck a codebase once a coding agent fixes every
  one, so a review prompt must define them and skip them. Reviewing with a
  model family other than the author's caught 10% more bugs. Shaped
  `pr-review` and `cross-review`.
- [Rate findings by likelihood and severity](https://x.com/Voxyz_ai/status/2115518965443076573)
  (Voxyz). Judge a finding by how likely and how harmful it is, so a rare but
  severe risk still gets fixed. Shaped the severity exception in
  `cross-review`'s Fix rule.

## Workflows

- [These 3 skills changed my life](https://youtu.be/5Bmp9cz1JN8) (Theo) and
  [t3dotgg/tstack](https://github.com/t3dotgg/tstack). Model-invokable skills
  with trigger-only descriptions that chain by phrase, and the `full-stop`,
  `babysit-pr`, `sol-loop`, and `file-pr` workflows. Shaped `full-stop`,
  `babysit-pr`, `cross-review`, and the description rules in `AGENTS.md`.
- [Google developer documentation style guide](https://developers.google.com/style/).
  The editorial reference behind `developer-documentation-style`.
- [Conventional Comments](https://conventionalcomments.org/) and
  [Conventional Branch](https://conventionalbranch.org/). The comment labels
  and branch names the review and Linear skills use.
- [mattpocock/skills](https://github.com/mattpocock/skills). General research,
  spec, TDD, and review skills, installed upstream instead of copied here.

## Earlier artifact-first workflow

These shaped the repository's first design, which
[ea8cfaa](https://github.com/gabrielrojasc/skills/commit/ea8cfaa) replaced.

- [Harness engineering](https://openai.com/index/harness-engineering) (OpenAI)
  and HumanLayer's
  [context engineering workshop](https://www.humanlayer.dev/docs/workshop) and
  [repository](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents).
  Durable plans in the repository, small entry points, and compacting context.
- [The necessary evolution of "Research, Plan, Implement"](https://betterquestions.ai/the-necessary-evolution-of-research-plan-implement-as-an-agentic-practice-in-2026/),
  [Making AI agents mainstream with Dexter Horthy](https://thehumansintheloop.substack.com/p/making-agents-mainstream-for-dev-with-dexter-horthy),
  [Advanced context engineering for coding agents](https://dev.to/ametel01/advanced-context-engineering-for-coding-agents-11p7),
  and HumanLayer's
  [commands](https://github.com/humanlayer/humanlayer/tree/main/.claude/commands)
  and [agents](https://github.com/humanlayer/humanlayer/tree/main/.claude/agents).
  The research, plan, and implement phases with separate locator and analyzer
  agents.
- [Benchmarks don't matter](https://forgecode.dev/blog/benchmarks-dont-matter/)
  (ForgeCode), its [repository](https://github.com/antinomyhq/forge), and the
  [Terminal-Bench 2.0 leaderboard](https://www.tbench.ai/leaderboard/terminal-bench/2.0).
  Seven agent failure modes and a doom-loop detector that reminds the agent
  when it repeats itself.
