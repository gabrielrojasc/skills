#!/usr/bin/env bash

set -euo pipefail

skill_dir="${1:-$(cd "$(dirname "$0")/.." && pwd -P)}"
fixture_dir="$(mktemp -d "${TMPDIR:-/tmp}/git-workspace-upstream.XXXXXX")"
fixture_dir="$(cd "$fixture_dir" && pwd -P)"
trap 'rm -rf "$fixture_dir"' EXIT

# Use only local fixture repositories and ignore personal Git configuration.
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_TERMINAL_PROMPT=0

run() {
  if ! "$@" >"${fixture_dir}/command.log" 2>&1; then
    cat "${fixture_dir}/command.log" >&2
    return 1
  fi
}

assert_upstream() {
  local actual
  actual="$(git -C "$1" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}')"
  if [ "$actual" != "$2" ]; then
    printf 'FAIL: expected upstream %s, got %s\n' "$2" "$actual" >&2
    return 1
  fi
}

assert_no_upstream() {
  local actual
  actual="$(git -C "$1" for-each-ref --format='%(upstream)' "refs/heads/$2")"
  if [ -n "$actual" ]; then
    printf 'FAIL: %s unexpectedly tracks %s\n' "$2" "$actual" >&2
    return 1
  fi
}

run git init --initial-branch=main "${fixture_dir}/remote"
run git -C "${fixture_dir}/remote" -c user.name=Fixture -c user.email=fixture@example.invalid \
  -c commit.gpgsign=false commit --allow-empty -m 'Fixture'

repos_root="${fixture_dir}/repos"
repo_path="${repos_root}/sample"
run bash "${skill_dir}/scripts/add-repo.sh" --repos-root "$repos_root" \
  --repo-name sample "${fixture_dir}/remote"
assert_upstream "${repo_path}/main" origin/main
printf 'PASS: clone sets default upstream\n'

run git -C "$repo_path" branch --unset-upstream main
run bash "${skill_dir}/scripts/add-repo.sh" --repos-root "$repos_root" \
  --repo-name sample "${fixture_dir}/remote"
assert_upstream "${repo_path}/main" origin/main
printf 'PASS: add-repo repairs missing default upstream\n'

run git -C "$repo_path" branch --unset-upstream main
run bash "${skill_dir}/scripts/sync-workspace.sh" --repos-root "$repos_root" --jobs 1 --no-prune
assert_upstream "${repo_path}/main" origin/main
printf 'PASS: sync repairs missing default upstream\n'

original_head="$(git -C "${repo_path}/main" rev-parse HEAD)"
run git -C "${repo_path}/main" switch -c feature/repair-check
run git -C "${fixture_dir}/remote" -c user.name=Fixture -c user.email=fixture@example.invalid \
  -c commit.gpgsign=false commit --allow-empty -m 'Advance remote'
run bash "${skill_dir}/scripts/add-repo.sh" --repos-root "$repos_root" \
  --repo-name sample "${fixture_dir}/remote"
[ "$(git -C "${repo_path}/main" symbolic-ref --short HEAD)" = main ]
[ "$(git -C "$repo_path" rev-parse feature/repair-check)" = "$original_head" ]
[ "$(git -C "${repo_path}/main" rev-parse HEAD)" = "$(git -C "$repo_path" rev-parse origin/main)" ]
printf 'PASS: repair restores default branch without advancing the task branch\n'

run git -C "${repo_path}/main" switch --detach "$original_head"
if bash "${skill_dir}/scripts/add-repo.sh" --repos-root "$repos_root" \
  --repo-name sample "${fixture_dir}/remote" >"${fixture_dir}/command.log" 2>&1; then
  printf 'FAIL: repair accepted a detached worktree\n' >&2
  exit 1
fi
[ "$(git -C "${repo_path}/main" rev-parse HEAD)" = "$original_head" ]
if git -C "${repo_path}/main" symbolic-ref --quiet HEAD; then
  printf 'FAIL: repair changed detached HEAD to a branch\n' >&2
  exit 1
fi
printf 'PASS: repair preserves detached HEAD\n'

run git -C "${repo_path}/main" switch feature/repair-check
printf 'uncommitted work\n' >"${repo_path}/main/local-work.txt"
if bash "${skill_dir}/scripts/add-repo.sh" --repos-root "$repos_root" \
  --repo-name sample "${fixture_dir}/remote" >"${fixture_dir}/command.log" 2>&1; then
  printf 'FAIL: repair accepted a dirty worktree\n' >&2
  exit 1
fi
[ "$(git -C "${repo_path}/main" symbolic-ref --short HEAD)" = feature/repair-check ]
[ "$(git -C "${repo_path}/main" rev-parse HEAD)" = "$original_head" ]
[ "$(cat "${repo_path}/main/local-work.txt")" = 'uncommitted work' ]
mv "${repo_path}/main/local-work.txt" "${fixture_dir}/preserved-work.txt"
run git -C "${repo_path}/main" switch main
printf 'PASS: repair preserves dirty worktree and branch\n'

for tracking_mode in true false always inherit simple; do
  run git -C "$repo_path" config branch.autoSetupMerge "$tracking_mode"
  run bash "${skill_dir}/scripts/create-task-worktree.sh" --repos-root "$repos_root" \
    --repo sample --task "tracking-${tracking_mode}"
  assert_no_upstream "$repo_path" "feature/tracking-${tracking_mode}"
  printf 'PASS: fresh task has no upstream with autoSetupMerge=%s\n' "$tracking_mode"
done

# Publishing establishes the matching upstream; reuse must preserve it.
run git -C "${repo_path}/tracking-true" push -u origin HEAD
assert_upstream "${repo_path}/tracking-true" origin/feature/tracking-true
run bash "${skill_dir}/scripts/create-task-worktree.sh" --repos-root "$repos_root" \
  --repo sample --task tracking-true
assert_upstream "${repo_path}/tracking-true" origin/feature/tracking-true
run git -C "$repo_path" worktree remove "${repo_path}/tracking-true"
run bash "${skill_dir}/scripts/create-task-worktree.sh" --repos-root "$repos_root" \
  --repo sample --task tracking-true
assert_upstream "${repo_path}/tracking-true" origin/feature/tracking-true
printf 'PASS: first push, reuse, and reattach preserve matching upstream\n'
