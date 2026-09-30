#!/usr/bin/env bash
# Run the full pr-review suite in Claude Code and Codex with the user's real
# configuration, then grade each run.
#
#   run-suite.sh <out-dir> [fixture...]     (default: every fixture with a grade.json)
#
# Runs go four at a time. Each cell's workspace holds its trace, rung scores,
# and grades; summary.txt collects them.
set -euo pipefail
here="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
out="${1:?out dir}"; shift
mkdir -p "$out"; out="$(CDPATH= cd -- "$out" && pwd -P)"
if [[ $# -gt 0 ]]; then fixtures=("$@"); else
  fixtures=(); for g in "$here"/fixtures/*/grade.json; do fixtures+=("$(basename "$(dirname "$g")")"); done
fi
cells=(); for f in "${fixtures[@]}"; do cells+=("claude $f" "codex $f"); done
run_cell() {
  local tool="$1" fixture="$2" ws="$3/$1-$2"
  "$4/run-rungs.sh" "$tool" "$ws" "$fixture" > "$3/$1-$2.rungs.log" 2>&1 || true
  python3 "$4/lib/grade.py" "$tool" "$ws" "$fixture" > "$3/$1-$2.grades.log" 2>&1 || true
}
export -f run_cell
printf '%s\n' "${cells[@]}" | xargs -P 4 -I{} bash -c 'set -- {}; run_cell "$1" "$2" "'"$out"'" "'"$here"'"'
: > "$out/summary.txt"
for c in "${cells[@]}"; do set -- $c; tail -1 "$out/$1-$2.grades.log" >> "$out/summary.txt"; done
cat "$out/summary.txt"
