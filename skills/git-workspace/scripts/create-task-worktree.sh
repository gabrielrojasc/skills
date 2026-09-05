#!/usr/bin/env bash

set -euo pipefail

script_name="${0##*/}"
repos_root="~/git"
branch_prefix="feature"
task_name=""
ticket_key=""
selected_repos=()

log_info() { printf 'info %s\n' "$1"; }
log_success() { printf 'success %s\n' "$1"; }
log_error() { printf 'error %s\n' "$1" >&2; }

usage() {
  cat <<EOF
Usage: ${script_name} [options] --repo <name> --task <name>

Create or reuse isolated task worktrees in bare-container repositories.

Options:
  --repos-root DIR        Repositories root (default: ${repos_root})
  --repo NAME             Repository container; repeatable
  --task NAME             Short task name
  --ticket KEY            Optional tracker key
  --branch-prefix PREFIX  Branch prefix (default: ${branch_prefix})
  -h, --help              Show this help
EOF
}

require_value() {
  if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
    log_error "$1 requires a value."
    exit 2
  fi
}

expand_home_path() {
  printf '%s' "${1/#\~/$HOME}"
}

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
    if [ "$existing" = "$name" ]; then
      return
    fi
  done
  selected_repos+=("$name")
}

detect_default_branch() {
  local repo_path="$1"

  git -C "$repo_path" remote set-head origin --auto >/dev/null 2>&1 || true
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

is_bare_container() {
  local repo_path="$1"
  [ -d "${repo_path}/.git" ] &&
    [ "$(git -C "$repo_path" rev-parse --is-bare-repository 2>/dev/null || printf 'false')" = "true" ]
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
branch_name="${branch_prefix}/${identifier}"
if ! git check-ref-format --branch "$branch_name" >/dev/null 2>&1; then
  log_error "Invalid branch name: ${branch_name}"
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
actions=()
default_branches=()

for repo_name in "${selected_repos[@]}"; do
  repo_path="${repos_root}/${repo_name}"
  worktree_path="${repo_path}/${identifier}"

  if [ ! -d "$repo_path" ] || ! is_bare_container "$repo_path"; then
    log_error "Not a bare-container repository: ${repo_path}"
    exit 1
  fi
  repo_real_path="$(physical_path "$repo_path")"
  if ! path_is_under "$repo_real_path" "$repos_root"; then
    log_error "Repository resolves outside the repositories root: ${repo_path} -> ${repo_real_path}"
    exit 1
  fi

  if git -C "$repo_path" worktree list --porcelain | grep -Fqx "worktree ${worktree_path}"; then
    current_branch="$(git -C "$worktree_path" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    if [ "$current_branch" != "$branch_name" ]; then
      log_error "Registered worktree uses ${current_branch}, expected ${branch_name}: ${worktree_path}"
      exit 1
    fi
    action="reuse"
    default_branch=""
  else
    if [ -e "$worktree_path" ]; then
      log_error "Path exists but is not the expected registered worktree: ${worktree_path}"
      exit 1
    fi

    if git -C "$repo_path" show-ref --verify --quiet "refs/heads/${branch_name}"; then
      if git -C "$repo_path" worktree list --porcelain | grep -Fqx "branch refs/heads/${branch_name}"; then
        log_error "Branch is already attached to another worktree: ${repo_name} ${branch_name}"
        exit 1
      fi
      action="attach"
      default_branch=""
    else
      if ! git -C "$repo_path" fetch --quiet --prune origin; then
        log_error "Fetch failed for ${repo_name}."
        exit 1
      fi
      default_branch="$(detect_default_branch "$repo_path" || true)"
      if [ -z "$default_branch" ]; then
        log_error "Cannot detect the default branch for ${repo_name}."
        exit 1
      fi
      action="create"
    fi
  fi

  repo_paths+=("$repo_path")
  worktree_paths+=("$worktree_path")
  actions+=("$action")
  default_branches+=("$default_branch")
done

created=0
reused=0
completed_indices=()

rollback_worktree() {
  local index="$1"
  local repo_path="${repo_paths[$index]}"
  local worktree_path="${worktree_paths[$index]}"
  local action="${actions[$index]}"
  local cleanup_failed=false

  if git -C "$repo_path" worktree list --porcelain | grep -Fqx "worktree ${worktree_path}"; then
    if ! git -C "$repo_path" worktree remove "$worktree_path" >/dev/null 2>&1; then
      log_error "Rollback could not remove ${worktree_path}."
      cleanup_failed=true
    fi
  elif [ -e "$worktree_path" ]; then
    log_error "Rollback found an unregistered path at ${worktree_path}; left it untouched."
    cleanup_failed=true
  fi

  if [ "$action" = "create" ] && [ "$cleanup_failed" = false ] &&
    git -C "$repo_path" show-ref --verify --quiet "refs/heads/${branch_name}"; then
    if git -C "$repo_path" worktree list --porcelain | grep -Fqx "branch refs/heads/${branch_name}"; then
      log_error "Rollback could not delete attached branch ${branch_name} in ${repo_path}."
      cleanup_failed=true
    elif ! git -C "$repo_path" branch -d -- "$branch_name" >/dev/null 2>&1; then
      log_error "Rollback could not delete ${branch_name} in ${repo_path}."
      cleanup_failed=true
    fi
  fi

  [ "$cleanup_failed" = false ]
}

rollback_created_worktrees() {
  local current_index="${1:-}"
  local position=""
  local index=""
  local rollback_failed=false

  if [ -n "$current_index" ] && ! rollback_worktree "$current_index"; then
    rollback_failed=true
  fi

  for ((position = ${#completed_indices[@]} - 1; position >= 0; position--)); do
    index="${completed_indices[$position]}"
    if ! rollback_worktree "$index"; then
      rollback_failed=true
    fi
  done

  if [ "$rollback_failed" = true ]; then
    log_error "Rollback was incomplete. Inspect the paths reported above."
  else
    log_info "Rolled back worktrees created by this invocation."
  fi
}

for i in "${!repo_paths[@]}"; do
  case "${actions[$i]}" in
    reuse)
      log_info "Reusing ${worktree_paths[$i]}"
      reused=$((reused + 1))
      ;;
    attach)
      if ! git -C "${repo_paths[$i]}" worktree add "${worktree_paths[$i]}" "$branch_name" >/dev/null; then
        log_error "Could not attach ${worktree_paths[$i]}."
        rollback_created_worktrees "$i"
        exit 1
      fi
      completed_indices+=("$i")
      log_success "Attached ${worktree_paths[$i]} to ${branch_name}"
      created=$((created + 1))
      ;;
    create)
      # The default branch is a starting point; the task upstream is set on first push.
      if ! git -C "${repo_paths[$i]}" worktree add --no-track "${worktree_paths[$i]}" -b "$branch_name" "origin/${default_branches[$i]}" >/dev/null; then
        log_error "Could not create ${worktree_paths[$i]}."
        rollback_created_worktrees "$i"
        exit 1
      fi
      completed_indices+=("$i")
      log_success "Created ${worktree_paths[$i]} from origin/${default_branches[$i]}"
      created=$((created + 1))
      ;;
  esac
done

printf '\nTask: %s\nBranch: %s\nCreated: %d\nReused: %d\n' "$identifier" "$branch_name" "$created" "$reused"
