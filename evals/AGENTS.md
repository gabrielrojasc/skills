# Evals

`pr-review/` drives real Claude Code and Codex runs against fixture PRs. The
headers of `run-suite.sh` and `run-rungs.sh` document their options.

Run every eval in both Claude Code and Codex.

`triggers/` checks which skill each tool picks for a prompt. Each case is a
`prompt.md` with one `tool_used: Skill` grader per skill that must fire
(`min: 1`) or stay silent (`max: 0`). `lib/codex.py` counts a Codex read of a
skill's `SKILL.md` as a Skill call, so both tools use the same graders. Write
prompts the way the user would ask, without naming the skill. Give each skill
at least one positive case, and add a near miss wherever a sibling skill or a
plain answer competes for the prompt.

Name a case `hard-*` when a realistic request makes the trigger hard to see:
the skill is one step of a larger task, the clue is only in the working
directory, or the request is terse. A case puts files in the working directory
through a `case.yaml` `scaffold_script` that calls `lib/scaffold.sh` with a
folder under `fixtures/`. Run hard cases with `--installed` too, and compare
against a run without it to tell a weak description from a competing skill.

## Test variants in isolation

Test a change to rung agents or global instructions in an isolated config, and
leave the user's live files untouched: other sessions read them during the run,
and an interrupted run can leave a variant in place.

- **Codex:** build a home that symlinks every entry of `~/.codex` except
  `agents/` and `AGENTS.md`, put the variant's copies of those two there, and
  run with `CODEX_HOME=<home>`. Auth, config, plugins, and `sessions/` stay
  shared, so `score-rungs.py` still finds the sessions. Variants with separate
  homes run in parallel. Before a full run, confirm the variant loaded: have
  `codex exec` quote the changed description, and grep its session file for the
  changed `AGENTS.md` line.
- **Claude Code:** `claude --agents '<json>'` overrides same-named user agents
  for one session. There is no verified way to swap the user's global
  instructions: `CLAUDE_CONFIG_DIR` logs out on macOS and drops
  `~/.claude.json`, and `--setting-sources project,local` also drops user skills
  and agents.
  `run-rungs.sh` doesn't pass `--agents` yet, and `score-rungs.py` reads Claude
  effort from `~/.claude/agents/`.

## Long runs

- Write output under `~/tmp/<skill>-evals/`, outside git (the runners refuse a
  git workspace) and outside `$TMPDIR`, which macOS purges.
- Start a suite under launchd with
  `launchctl submit -l <label> -o <log> -e <log> -- /usr/bin/env PATH="$PATH" /bin/bash -c '<command>'`,
  and `launchctl remove <label>` once it finishes, because launchd restarts a
  submitted job when it exits. Pass `PATH` through `env`: a launchd login
  shell doesn't get the user's, and finds neither `claude` nor `codex`. Claude
  Code stops its background tasks after about 30 minutes and kills even
  `setsid` children when its session restarts. Poll with waits under 25
  minutes.
- Claude Code cells and the Opus judge share the user's 5-hour session limit:
  18 Claude cells at once exhausted it in one full suite. Run Claude with a
  lower `JOBS` than Codex.
- `codex exec` can hang after a transient model or network failure: its trace
  stops growing for 20 minutes or more while sibling cells progress. Match the
  process to its cell by working directory (`lsof -p <pid> | rg cwd`) before
  stopping it, then rerun the cell.
