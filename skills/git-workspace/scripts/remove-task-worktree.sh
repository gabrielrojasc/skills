#!/usr/bin/env bash

set -euo pipefail

script_name="${0##*/}"
repos_root="~/git"
branch_prefix="feature"
task_name=""
ticket_key=""
skip_confirm=false
selected_repos=()

log_info() { printf 'info %s\n' "$1"; }
log_success() { printf 'success %s\n' "$1"; }
log_warning() { printf 'warning %s\n' "$1" >&2; }
log_error() { printf 'error %s\n' "$1" >&2; }

usage() {
  cat <<EOF
Usage: ${script_name} [options] --repo <name> --task <name>

Remove exact task worktrees after safety checks and confirmation.

Options:
  --repos-root DIR        Repositories root (default: ${repos_root})
  --repo NAME             Repository container; repeatable
  --task NAME             Short task name
  --ticket KEY            Optional tracker key
  --branch-prefix PREFIX  Branch prefix (default: ${branch_prefix})
  --yes                   Skip the confirmation prompt after external approval
  -h, --help              Show this help
EOF
}

require_value() {
  if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
    log_error "$1 requires a value."
    exit 2
  fi
}

expand_home_path() { printf '%s' "${1/#\~/$HOME}"; }

slugify() {
  printf '%s' "$1" |
    tr '[:upper:]' '[:lower:]' |
    sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
}

add_repo() {
  local name="$1"
  local existing=""
  case "$name" in
    "" | . | .. | */*)
      log_error "Unsafe repository name: ${name}"
      exit 2
      ;;
  esac
  for existing in "${selected_repos[@]:-}"; do
    [ "$existing" = "$name" ] && return
  done
  selected_repos+=("$name")
}

detect_default_branch() {
  local repo_path="$1"
  if git -C "$repo_path" symbolic-ref --short refs/remotes/origin/HEAD >/dev/null 2>&1; then
    git -C "$repo_path" symbolic-ref --short refs/remotes/origin/HEAD | sed 's@^origin/@@'
  elif git -C "$repo_path" rev-parse --verify 'refs/remotes/origin/main^{commit}' >/dev/null 2>&1; then
    printf 'main'
  elif git -C "$repo_path" rev-parse --verify 'refs/remotes/origin/master^{commit}' >/dev/null 2>&1; then
    printf 'master'
  else
    return 1
  fi
}

physical_path() {
  (
    cd "$1" >/dev/null 2>&1 &&
      pwd -P
  )
}

path_is_under() {
  case "${1}/" in
    "${2}/"*) return 0 ;;
    *) return 1 ;;
  esac
}

unpushed_count() {
  local worktree_path="$1"
  local branch_name="$2"
  local upstream=""
  local default_branch=""

  if upstream="$(git -C "$worktree_path" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)"; then
    git -C "$worktree_path" rev-list --count "${upstream}..HEAD"
  elif git -C "$worktree_path" rev-parse --verify "refs/remotes/origin/${branch_name}^{commit}" >/dev/null 2>&1; then
    git -C "$worktree_path" rev-list --count "origin/${branch_name}..HEAD"
  elif default_branch="$(detect_default_branch "$worktree_path")"; then
    git -C "$worktree_path" rev-list --count "origin/${default_branch}..HEAD"
  else
    return 1
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repos-root)
      require_value "$@"
      repos_root="$2"
      shift 2
      ;;
    --repo)
      require_value "$@"
      add_repo "$2"
      shift 2
      ;;
    --task)
      require_value "$@"
      task_name="$2"
      shift 2
      ;;
    --ticket)
      require_value "$@"
      ticket_key="$2"
      shift 2
      ;;
    --branch-prefix)
      require_value "$@"
      branch_prefix="$2"
      shift 2
      ;;
    --yes)
      skip_confirm=true
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      log_error "Unknown argument: $1"
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$task_name" ] || [ "${#selected_repos[@]}" -eq 0 ]; then
  log_error "Pass --task and at least one --repo."
  usage >&2
  exit 2
fi

case "$branch_prefix" in
  "" | . | .. | -* | */* | *[!A-Za-z0-9._-]*)
    log_error "Unsafe branch prefix: ${branch_prefix}"
    exit 2
    ;;
esac

identifier="$(slugify "${ticket_key:+${ticket_key}-}${task_name}")"
if [ -z "$identifier" ]; then
  log_error "Task and ticket do not produce a safe worktree name."
  exit 2
fi
expected_branch="${branch_prefix}/${identifier}"
if ! git check-ref-format --branch "$expected_branch" >/dev/null 2>&1; then
  log_error "Invalid branch name: ${expected_branch}"
  exit 2
fi

repos_root="$(expand_home_path "$repos_root")"
if [ ! -d "$repos_root" ]; then
  log_error "Repositories root does not exist: ${repos_root}"
  exit 1
fi
repos_root="$(cd "$repos_root" && pwd -P)"

repo_paths=()
worktree_paths=()
branches=()

for repo_name in "${selected_repos[@]}"; do
  repo_path="${repos_root}/${repo_name}"
  worktree_path="${repo_path}/${identifier}"

  if [ ! -d "$repo_path" ] || [ "$(git -C "$repo_path" rev-parse --is-bare-repository 2>/dev/null || printf 'false')" != "true" ]; then
    log_error "Not a bare-container repository: ${repo_path}"
    exit 1
  fi
  repo_real_path="$(physical_path "$repo_path")"
  if ! path_is_under "$repo_real_path" "$repos_root"; then
    log_error "Repository resolves outside the repositories root: ${repo_path} -> ${repo_real_path}"
    exit 1
  fi

  if ! git -C "$repo_path" worktree list --porcelain | grep -Fqx "worktree ${worktree_path}"; then
    if [ -e "$worktree_path" ]; then
      log_error "Path exists but is not a registered task worktree: ${worktree_path}"
      exit 1
    fi
    log_info "No matching worktree in ${repo_name}; skipping."
    continue
  fi

  branch="$(git -C "$worktree_path" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [ "$branch" != "$expected_branch" ]; then
    log_error "Worktree uses ${branch}, expected ${expected_branch}: ${worktree_path}"
    exit 1
  fi

  if [ -n "$(git -C "$worktree_path" status --porcelain)" ]; then
    log_error "Worktree has uncommitted changes: ${worktree_path}"
    exit 1
  fi

  if ! git -C "$repo_path" fetch --quiet --prune origin; then
    log_error "Fetch failed for ${repo_name}; cannot verify pushed commits."
    exit 1
  fi

  ahead="$(unpushed_count "$worktree_path" "$branch" || true)"
  if ! [[ "$ahead" =~ ^[0-9]+$ ]]; then
    log_error "Cannot determine whether ${branch} has unpushed commits."
    exit 1
  fi
  if [ "$ahead" -gt 0 ]; then
    log_error "Branch has ${ahead} unpushed commit(s): ${repo_name} ${branch}"
    exit 1
  fi

  repo_paths+=("$repo_path")
  worktree_paths+=("$worktree_path")
  branches+=("$branch")
done

if [ "${#worktree_paths[@]}" -eq 0 ]; then
  log_info "No matching task worktrees found."
  exit 0
fi

printf 'Cleanup plan:\n'
for i in "${!worktree_paths[@]}"; do
  printf '  - %s, branch %s\n' "${worktree_paths[$i]}" "${branches[$i]}"
done

if [ "$skip_confirm" != true ]; then
  printf 'Proceed? [y/N] '
  read -r answer
  case "$answer" in
    y | Y) ;;
    *)
      log_info "Aborted."
      exit 0
      ;;
  esac
fi

failed=0
for i in "${!worktree_paths[@]}"; do
  if git -C "${repo_paths[$i]}" worktree remove "${worktree_paths[$i]}"; then
    log_success "Removed ${worktree_paths[$i]}"
    if git -C "${repo_paths[$i]}" branch -d -- "${branches[$i]}"; then
      log_success "Deleted ${branches[$i]}"
    else
      log_warning "Worktree removed, but safe branch deletion refused ${branches[$i]}."
      failed=1
    fi
  else
    log_error "Could not remove ${worktree_paths[$i]}."
    failed=1
  fi
done

exit "$failed"
