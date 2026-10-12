#!/usr/bin/env bash
# Copy a fixture into the run's working directory.
#
#   scaffold.sh <fixture> [branch]
#
# With a branch, make the copy a Git repository on that branch with an
# acme/widgets origin.
set -euo pipefail
[[ $# -gt 0 ]] || { echo "usage: scaffold.sh <fixture> [branch]" >&2; exit 2; }
lib="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
cp -R "${lib}/../fixtures/$1/." .
if [[ $# -gt 1 ]]; then
  git=(git -c user.name=eval -c user.email=eval@example.com -c commit.gpgsign=false)
  "${git[@]}" init -q -b main
  "${git[@]}" add -A
  "${git[@]}" commit -q -m "chore: initial commit"
  "${git[@]}" checkout -q -b "$2"
  "${git[@]}" remote add origin https://github.com/acme/widgets.git
fi
