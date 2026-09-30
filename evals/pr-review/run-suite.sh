#!/usr/bin/env bash
# Run the full pr-review suite in Claude Code and Codex with the user's real
# configuration, then grade each run.
#
#   run-suite.sh <out-dir> [fixture...]     (default: every fixture with a grade.json)
#
# Runs go four at a time. RUNS=<n> repeats every cell n times under
# <out-dir>/r<i>/. Each cell's workspace holds its trace, rung scores, grades,
# and elapsed seconds; summary.txt collects them.
set -euo pipefail
here="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
out="${1:?out dir}"; shift
mkdir -p "$out"; out="$(CDPATH= cd -- "$out" && pwd -P)"
if [[ $# -gt 0 ]]; then fixtures=("$@"); else
  fixtures=(); for g in "$here"/fixtures/*/grade.json; do fixtures+=("$(basename "$(dirname "$g")")"); done
fi
runs="${RUNS:-1}"
cells=()
for ((r = 1; r <= runs; r++)); do
  dir="$out"; [[ "$runs" -gt 1 ]] && dir="$out/r$r"
  mkdir -p "$dir"
  for f in "${fixtures[@]}"; do cells+=("claude $f $dir" "codex $f $dir"); done
done
run_cell() {
  local tool="$1" fixture="$2" dir="$3" ws="$3/$1-$2" start=$SECONDS
  "$4/run-rungs.sh" "$tool" "$ws" "$fixture" > "$dir/$1-$2.rungs.log" 2>&1 || true
  echo $((SECONDS - start)) > "$ws/elapsed"
  python3 "$4/lib/grade.py" "$tool" "$ws" "$fixture" > "$dir/$1-$2.grades.log" 2>&1 || true
}
export -f run_cell
printf '%s\n' "${cells[@]}" | xargs -P 4 -I{} bash -c 'set -- {}; run_cell "$1" "$2" "$3" "'"$here"'"'
: > "$out/summary.txt"
for c in "${cells[@]}"; do
  set -- $c
  echo "$(tail -1 "$3/$1-$2.grades.log") in $(cat "$3/$1-$2/elapsed" 2>/dev/null || echo '?')s" >> "$out/summary.txt"
done
cat "$out/summary.txt"
