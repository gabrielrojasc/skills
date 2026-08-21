#!/usr/bin/env bash

set -euo pipefail

script_name="${0##*/}"

color_reset=""
color_red=""
color_yellow=""
color_green=""
color_blue=""
color_bold=""
color_dim=""

if [ -t 1 ] && [ "${TERM:-}" != "dumb" ] && command -v tput >/dev/null 2>&1; then
  colors="$(tput colors 2>/dev/null || printf '0')"
  if [ "${colors:-0}" -ge 8 ]; then
    color_reset="$(tput sgr0)"
    color_red="$(tput setaf 1)"
    color_yellow="$(tput setaf 3)"
    color_green="$(tput setaf 2)"
    color_blue="$(tput setaf 4)"
    color_bold="$(tput bold)"
    color_dim="$(tput dim 2>/dev/null || printf '')"
  fi
fi

log_info() {
  printf '%s%sinfo%s %s\n' "${color_blue}" "${color_bold}" "${color_reset}" "$1"
}

log_warning() {
  printf '%s%swarning%s %s\n' "${color_yellow}" "${color_bold}" "${color_reset}" "$1" >&2
}

log_error() {
  printf '%s%serror%s %s\n' "${color_red}" "${color_bold}" "${color_reset}" "$1" >&2
}

repos_root="~/git"

usage() {
  cat <<EOF
Usage: ${script_name} [options]

List bare-container repositories and their task worktrees.

Options:
  --repos-root DIR  Repositories root (default: ${repos_root})
  -h, --help        Show this help
EOF
  exit "${1:-0}"
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

is_bare_container() {
  local repo_path="$1"

  [ -d "${repo_path%/}/.git" ] || return 1
  [ "$(git -C "$repo_path" rev-parse --is-bare-repository 2>/dev/null || printf 'false')" = "true" ]
}

detect_default_branch() {
  local repo_path="$1"

  if git -C "$repo_path" symbolic-ref --short refs/remotes/origin/HEAD >/dev/null 2>&1; then
    git -C "$repo_path" symbolic-ref --short refs/remotes/origin/HEAD | sed 's@^origin/@@'
    return 0
  fi

  if git -C "$repo_path" rev-parse --verify "refs/remotes/origin/main^{commit}" >/dev/null 2>&1; then
    printf 'main'
    return 0
  fi

  if git -C "$repo_path" rev-parse --verify "refs/remotes/origin/master^{commit}" >/dev/null 2>&1; then
    printf 'master'
    return 0
  fi

  return 1
}

task_found=0

emit_worktree() {
  local wt_path="$1"
  local branch_ref="$2"
  local wt_base=""
  local branch=""
  local dirty=""

  [ -n "$wt_path" ] || return 0
  wt_base="$(basename "$wt_path")"

  if [ "$wt_path" = "${repo_path%/}" ] || [ "$wt_path" = "${repo_path%/}/${default_branch}" ]; then
    return 0
  fi

  case "$branch_ref" in
    refs/heads/*) branch="${branch_ref#refs/heads/}" ;;
    *) branch="(detached)" ;;
  esac

  if [ -d "$wt_path" ] && [ -n "$(git -C "$wt_path" status --porcelain 2>/dev/null)" ]; then
    dirty=" ${color_yellow}[dirty]${color_reset}"
  fi

  printf '  %s -> %s%s\n' "$wt_base" "$branch" "$dirty"
  task_found=$((task_found + 1))
  worktree_count=$((worktree_count + 1))
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repos-root)
      require_value "$@"
      repos_root="$2"
      shift 2
      ;;
    -h | --help)
      usage 0
      ;;
    -*)
      log_error "Unknown option: $1"
      usage 1
      ;;
    *)
      log_error "Unexpected argument: $1"
      usage 1
      ;;
  esac
done

repos_root="$(expand_home_path "$repos_root")"

if [ ! -d "$repos_root" ]; then
  log_error "Repos root does not exist: ${repos_root}"
  exit 1
fi

repos_root="$(cd "$repos_root" >/dev/null 2>&1 && pwd -P)"

container_count=0
worktree_count=0
non_container=()

printf '%s%sWorkspace%s %s\n\n' "${color_bold}" "${color_blue}" "${color_reset}" "$repos_root"

for repo_path in "$repos_root"/*/; do
  [ -d "$repo_path" ] || continue
  repo_name="$(basename "$repo_path")"

  if ! is_bare_container "$repo_path"; then
    non_container+=("$repo_name")
    continue
  fi

  container_count=$((container_count + 1))

  default_branch="$(detect_default_branch "$repo_path" || printf 'unknown')"
  printf '%s%s%s %s(default: %s)%s\n' \
    "${color_bold}" "$repo_name" "${color_reset}" \
    "${color_dim}" "$default_branch" "${color_reset}"

  task_found=0
  current_wt=""
  current_branch=""

  while IFS= read -r line || [ -n "$line" ]; do
    if [ -z "$line" ]; then
      emit_worktree "$current_wt" "$current_branch"
      current_wt=""
      current_branch=""
      continue
    fi

    case "$line" in
      worktree\ *) current_wt="${line#worktree }" ;;
      branch\ *) current_branch="${line#branch }" ;;
    esac
  done < <(git -C "$repo_path" worktree list --porcelain)
  emit_worktree "$current_wt" "$current_branch"

  if [ "$task_found" -eq 0 ]; then
    printf '  %s(no task worktrees)%s\n' "${color_dim}" "${color_reset}"
  fi
done

if [ "${#non_container[@]}" -gt 0 ]; then
  printf '\n%sNot bare-container repos%s\n' "${color_dim}" "${color_reset}"
  for name in "${non_container[@]}"; do
    printf '  %s\n' "$name"
  done
fi

printf '\n%s%sSummary%s\n' "${color_bold}" "${color_blue}" "${color_reset}"
printf 'Repo containers:      %d\n' "$container_count"
printf 'Task worktrees:       %d\n' "$worktree_count"
