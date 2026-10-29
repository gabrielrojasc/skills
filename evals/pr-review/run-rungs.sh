#!/usr/bin/env bash
# Run pr-review headless on fixture PRs in Claude Code or Codex with the user's
# real configuration, then score which model and effort ran each review role.
#
#   run-rungs.sh <claude|codex> <out-dir> <fixture>...
#
# RUNG_POLICY=tier2-reviewers scores normal PRs' reviewers against tier 2
# instead of tier 3 (see lib/score-rungs.py).
#
# Each fixture is a folder under fixtures/, or under $FIXTURES when set. Several fixtures make one batch
# request, followed by each fixture's optional `instructions` file, such as a
# dispatcher's constraints. Nothing is posted: the fake gh records writes under
# posted/.
set -euo pipefail
tool="${1:?tool}"; out="${2:?out dir}"; shift 2
here="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
fx="${FIXTURES:-${here}/fixtures}"
mkdir -p "$out"; out="$(CDPATH= cd -- "$out" && pwd -P)"
cd "$out"
# A workspace inside a git repo makes agents sync or review that repo instead.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: ${out} is inside a git repository; use a directory outside any repo" >&2
  exit 2
fi
"${here}/lib/scaffold.sh" "$@"
refs=(); expect=()
for fixture in "$@"; do
  n="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["number"])' "${fx}/${fixture}/pr.json")"
  risk="$(cat "${fx}/${fixture}/risk")"
  repo="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["repository"]["nameWithOwner"])' "${fx}/${fixture}/pr.json")"
  refs+=("${repo}#${n}"); expect+=("${n}=${risk}")
done
prompt="Use the pr-review skill to review ${refs[*]}."
for fixture in "$@"; do
  extra="${fx}/${fixture}/instructions"
  if [[ -f "$extra" ]]; then prompt+=$'\n\n'"$(cat "$extra")"; fi
done
# Agents run commands in a login shell; a private ZDOTDIR keeps the fake gh first
# on PATH. If the real gh or git still runs, it gets no GitHub credentials: a
# bogus token for gh, and no global git config (credential helper) or SSH for git.
mkdir -p zdot ghconfig; printf 'export PATH="%s/bin:$PATH"\n' "$out" | tee zdot/.zprofile > zdot/.zshrc
export ZDOTDIR="${out}/zdot" GH_CONFIG_DIR="${out}/ghconfig" GH_TOKEN=pr-review-eval-no-access
export GIT_CONFIG_GLOBAL=/dev/null GIT_SSH_COMMAND=false GIT_TERMINAL_PROMPT=0
if [[ "$tool" == claude ]]; then
  PATH="${out}/bin:${PATH}" CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 claude -p "$prompt" --output-format stream-json --verbose \
    --max-budget-usd "${MAX_BUDGET_USD:-10}" --permission-mode acceptEdits \
    --allowedTools "Bash Read Write Edit Glob Grep Skill Agent mcp__claude_ai_Linear__get_issue mcp__claude_ai_Linear__list_comments mcp__claude_ai_Linear__search_documentation" --no-session-persistence \
    < /dev/null > trace.jsonl 2> stderr.log
else
  codex exec --skip-git-repo-check -s workspace-write --json -o final.md "$prompt" \
    < /dev/null > trace.jsonl 2> stderr.log
fi
python3 "${here}/lib/score-rungs.py" "$tool" trace.jsonl --expect "${expect[@]}" --policy "${RUNG_POLICY:-current}" --json scores.json | tee scores.txt
