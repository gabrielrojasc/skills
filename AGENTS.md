# Repository guidance

## Scope

- This repository owns Gabriel's portable personal agent skills.
- Maintain this repository in its existing `main` checkout. Create a branch or
  worktree only when the user asks for one.
- Install third-party skills from their upstream repositories. Keep their source
  out of this repository.
- Keep project-specific skills in the project that owns their assumptions and
  tooling.

## Skill structure

- Put each installable skill under `skills/<name>/` or
  `skills/<category>/<name>/`. Keep ZeroFox-specific skills under
  `skills/zerofox/`.
- Give every skill a `SKILL.md` whose frontmatter name matches its directory.
- Add `agents/openai.yaml` for Codex display metadata and invocation policy.
- Write each description as one compact, unquoted `Use when <trigger>.`
  sentence. Name the domain in the trigger, such as "Linear work" or "a
  GitHub PR", since no summary of what the skill does precedes it. Keep the
  `SKILL.md` description and `agents/openai.yaml`
  `interface.short_description` identical so agents receive the same trigger
  from either source.
- Keep ordered agent steps in `SKILL.md`. Move branch-specific reference
  material behind a direct pointer under `references/`.
- Put repeatable mechanics in `scripts/`. Keep cross-task policy in the
  user-level `AGENTS.md` and domain-specific workflow in the skill that triggers
  it.
- Copy a script into each skill that uses it, so every skill installs on its
  own. When you change a script, find same-named copies under `skills/` and
  keep them identical.
- Leave every skill model-invokable, so one request can chain several skills
  by their triggers, as in "take it over, full stop". When a related task
  shouldn't start the skill, as with one that pushes or runs unattended, key
  the trigger to an explicit request: "Use when asked to babysit a GitHub PR."
- Add a subagent step only for work the user-level `AGENTS.md` "Multi-agent
  work" section says to delegate. Keep sequential steps that share state in
  the main agent, and start one subagent per shared context, such as one
  challenger per PR, not one per item. Background:
  [When to fold subagents into your main agent loop](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop).
- Key every trigger and stop condition to something the agent can observe when
  it decides: the kind of task, a tool, or a fact in its record. "When you'll
  make 10+ tool calls" fails because the agent can't know the count beforehand.
  When a stop rule compares rounds, have each round report what it compares.

## Change rules

- Wrap Markdown prose at 80 columns. Leave headings, tables, code blocks, and
  links that can't break as they are.
- Match the concision of the surrounding skill text. Write only what changes
  agent behavior; leave out what agents already know or would recover from on
  their own.
- Keep `README.md` and the skill inventory in sync.
- When a changed skill has a same-named skill in `riskive/ai-tooling`, propose
  the matching team PR. The team copy may differ from this one.
- Run `scripts/validate-skills.sh` after changing skills, metadata, or scripts.
- When you add, rename, or change the description or invocation policy of a
  model-invoked skill, keep its link in `evals/triggers/skills/` and its cases
  in `evals/triggers/evals/` current, then propose running
  `evals/triggers/run-evals.sh --case '*<name>*'`.
- Treat every eval run as a gate. Show the command and the cases it covers,
  and start it only after the user approves that run. An approval covers one
  run: a rerun, a wider case set, or a fallback for a tool that failed each
  needs its own approval, even later in the same session.
- Run every approved eval in both Claude Code and Codex, and report both tools'
  results. A result from one tool doesn't stand in for the other.
- Preserve approval gates for external writes and for removing worktrees or
  deleting branches that hold unmerged work.
- Do not change global installations, global agent guidance, or external
  services as part of a repository edit without explicit approval.
