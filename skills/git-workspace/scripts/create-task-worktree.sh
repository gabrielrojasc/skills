#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
exec python3 -B "${script_dir}/workspace.py" create-task-worktree "$@"
