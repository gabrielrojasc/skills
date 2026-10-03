# Evals

Each eval drives real Claude Code and Codex runs against fixture PRs. The
headers of `run-suite.sh` and `run-rungs.sh` document their options.

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
- Start a suite detached with
  `perl -e 'use POSIX qw(setsid); setsid(); exec @ARGV' <command> &`. Claude
  Code stops its background tasks after about 30 minutes, so poll with waits
  under 25.
- `codex exec` can hang after a transient model or network failure: its trace
  stops growing for 20 minutes or more while sibling cells progress. Match the
  process to its cell by working directory (`lsof -p <pid> | rg cwd`) before
  stopping it, then rerun the cell.
