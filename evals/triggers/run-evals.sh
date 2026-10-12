#!/usr/bin/env bash
# Check that each model-invoked skill fires on the prompts it should and stays
# silent on near misses, in Claude Code and Codex at once.
#
#   run-evals.sh [out-dir] [--installed] [--case GLOB] [--runs N] [-j N]
#
# out-dir defaults to ~/tmp/trigger-evals/<timestamp>. Each tool's runs see only
# its built-in skills and the ones linked under skills/, not the user's global
# instructions. --installed also loads every skill in ~/.agents/skills that this
# repository doesn't own, so the repo skills compete with them as in real use.
# Claude runs through `claude plugin eval` with the no-plugin baseline off, since
# that arm has no skills to fire. lib/codex.py runs the same cases in Codex.
# Cases named hard-* are reported separately and don't affect the exit status.
set -euo pipefail

here="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
out="${HOME}/tmp/trigger-evals/$(date +%Y%m%dT%H%M%S)"
if [[ $# -gt 0 && "$1" != -* ]]; then out="$1"; shift; fi
# launchd restarts a finished job, which would overwrite this run's results.
if [[ -n "$(ls -A "$out" 2>/dev/null)" ]]; then
  echo "error: ${out} is not empty; pass a new out-dir" >&2
  exit 2
fi
mkdir -p "$out/claude"; out="$(CDPATH= cd -- "$out" && pwd -P)"
installed=false; case_glob='*'; runs=3; jobs=4
while [[ $# -gt 0 ]]; do
  case "$1" in
    --installed) installed=true; shift ;;
    --case) case_glob="$2"; shift 2 ;;
    --runs) runs="$2"; shift 2 ;;
    -j) jobs="$2"; shift 2 ;;
    *) echo "error: unknown option $1" >&2; exit 2 ;;
  esac
done
flags=(--case "$case_glob" --runs "$runs" -j "$jobs")
recorded=("${flags[@]}"); $installed && recorded=(--installed "${flags[@]}")
printf '%q ' "$0" "$out" "${recorded[@]}" > "$out/command.txt"; echo >> "$out/command.txt"

# `claude plugin eval` refuses manifests and case folders reached through links
# that leave the plugin, so each run gets a copy, which also records what ran.
plugin="$out/plugin"
mkdir -p "$plugin/skills"
cp -R "$here/.claude-plugin" "$here/bin" "$here/evals" "$here/fixtures" "$here/lib" "$plugin/"
rm -rf "$plugin/evals/results"
for link in "$here"/skills/*; do ln -sfn "$(cd "$link" && pwd -P)" "$plugin/skills/$(basename "$link")"; done
if $installed; then
  owned=" $(cd "$here/../../skills" && find . -name SKILL.md -exec dirname {} \; | xargs -n1 basename | tr '\n' ' ')"
  for skill in "$HOME"/.agents/skills/*/; do
    name="$(basename "$skill")"
    [[ "$owned" == *" $name "* ]] || ln -sfn "$(cd "$skill" && pwd -P)" "$plugin/skills/$name"
  done
fi

(cd "$plugin" && PATH="$plugin/bin:$PATH" claude plugin eval . --no-publish --trust-plugin --ablation none \
  --scaffold --allow-tools Bash "${flags[@]}" --output-dir "$out/claude" \
  --json "$out/claude/result.json" --report "$out/claude/report.html" --threshold 0 \
  > "$out/claude/eval.log" 2>&1) &
claude_pid=$!
python3 "$plugin/lib/codex.py" "$out/codex" --skills "$plugin/skills" "${flags[@]}" \
  > "$out/codex.log" 2>&1 || true
wait "$claude_pid" || true

echo "results: $out"
python3 "$here/lib/summary.py" "$out/claude/result.json" "$out/codex/summary.json" | tee "$out/summary.txt"
