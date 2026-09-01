#!/usr/bin/env bash

set -euo pipefail

script_name="${0##*/}"

color_reset=""
color_red=""
color_yellow=""
color_green=""
color_blue=""
color_bold=""

if [ -t 1 ] && [ "${TERM:-}" != "dumb" ] && command -v tput >/dev/null 2>&1; then
  colors="$(tput colors 2>/dev/null || printf '0')"
  if [ "${colors:-0}" -ge 8 ]; then
    color_reset="$(tput sgr0)"
    color_red="$(tput setaf 1)"
    color_yellow="$(tput setaf 3)"
    color_green="$(tput setaf 2)"
    color_blue="$(tput setaf 4)"
    color_bold="$(tput bold)"
  fi
fi

log_info() {
  printf '%s%sinfo%s %s\n' "${color_blue}" "${color_bold}" "${color_reset}" "$1"
}

log_success() {
  printf '%s%ssuccess%s %s\n' "${color_green}" "${color_bold}" "${color_reset}" "$1"
}

log_warning() {
  printf '%s%swarning%s %s\n' "${color_yellow}" "${color_bold}" "${color_reset}" "$1" >&2
}

log_error() {
  printf '%s%serror%s %s\n' "${color_red}" "${color_bold}" "${color_reset}" "$1" >&2
}

repos_root="~/git"
parallel_jobs=""
do_prune=true

usage() {
  cat <<EOF
Usage: ${script_name} [options]

Fetch each bare-container repo, fast-forward its default-branch worktree, and
prune stale worktree registrations. Task worktrees are never modified.

Options:
  --repos-root DIR  Repositories root (default: ${repos_root})
  --jobs N          Max parallel repos (default: auto, capped at 8)
  --no-prune        Skip 'git worktree prune'
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

resolve_default_branch() {
  local repo_path="$1"

  git -C "$repo_path" remote set-head origin --auto >/dev/null 2>&1 || true

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

configure_default_branch_tracking() {
  local repo_path="$1"
  local default_branch="$2"

  git -C "$repo_path" branch --set-upstream-to="origin/${default_branch}" "$default_branch" >/dev/null
}

default_parallel_jobs() {
  local cpu_count=""

  if command -v getconf >/dev/null 2>&1; then
    cpu_count="$(getconf _NPROCESSORS_ONLN 2>/dev/null || true)"
  fi

  if [ -z "$cpu_count" ] && command -v nproc >/dev/null 2>&1; then
    cpu_count="$(nproc 2>/dev/null || true)"
  fi

  if [ -z "$cpu_count" ] && command -v sysctl >/dev/null 2>&1; then
    cpu_count="$(sysctl -n hw.logicalcpu 2>/dev/null || true)"
  fi

  if ! [[ "$cpu_count" =~ ^[0-9]+$ ]] || [ "$cpu_count" -lt 1 ]; then
    cpu_count=4
  fi

  if [ "$cpu_count" -gt 8 ]; then
    cpu_count=8
  fi

  printf '%s' "$cpu_count"
}

running_job_count() {
  jobs -pr | wc -l | tr -d ' '
}

wait_for_available_slot() {
  local max_jobs="$1"

  while [ "$(running_job_count)" -ge "$max_jobs" ]; do
    sleep 0.1
  done
}

sync_repo() {
  local repo_path="$1"
  local repo_name="$2"
  local log_file="$3"
  local status_file="$4"
  local outcome="failed"
  local default_branch=""
  local default_wt=""
  local current_branch=""
  local worktree_status=""
  local local_head=""
  local remote_head=""

  {
    if ! git -C "$repo_path" fetch --prune --quiet origin; then
      log_warning "${repo_name}: fetch failed"
      printf '%s\n' "$outcome" >"$status_file"
      return 0
    fi

    if ! default_branch="$(resolve_default_branch "$repo_path")"; then
      log_warning "${repo_name}: cannot detect default branch"
      printf '%s\n' "$outcome" >"$status_file"
      return 0
    fi

    default_wt="${repo_path%/}/${default_branch}"

    if ! git -C "$repo_path" worktree list --porcelain | grep -Fqx "worktree ${default_wt}"; then
      log_warning "${repo_name}: default worktree missing (run add-repo.sh to repair)"
      outcome="skipped"
    elif [ ! -d "$default_wt" ]; then
      log_warning "${repo_name}: default worktree registered but path is gone (run add-repo.sh to repair)"
      outcome="skipped"
    elif ! worktree_status="$(git -C "$default_wt" status --porcelain)"; then
      log_warning "${repo_name}: could not inspect default worktree"
      outcome="skipped"
    elif [ -n "$worktree_status" ]; then
      log_warning "${repo_name}: default worktree has local changes; skipping repair and fast-forward"
      outcome="skipped"
    else
      current_branch="$(
        git -C "$default_wt" symbolic-ref --quiet --short HEAD 2>/dev/null ||
          true
      )"

      if [ -z "$current_branch" ]; then
        log_warning "${repo_name}: default worktree has a detached HEAD; skipping automatic repair"
        outcome="skipped"
      elif [ "$current_branch" != "$default_branch" ] &&
        ! git -C "$default_wt" switch --quiet "$default_branch"; then
        log_warning "${repo_name}: could not restore ${default_branch}; it may be checked out elsewhere"
        outcome="skipped"
      else
        if [ "$current_branch" != "$default_branch" ]; then
          log_success "${repo_name}: restored ${default_branch} from ${current_branch}"
        fi

        if ! configure_default_branch_tracking "$repo_path" "$default_branch"; then
          log_warning "${repo_name}: could not set ${default_branch} to track origin/${default_branch}"
          outcome="skipped"
        else
          local_head="$(git -C "$default_wt" rev-parse HEAD 2>/dev/null || true)"
          remote_head="$(git -C "$default_wt" rev-parse "origin/${default_branch}" 2>/dev/null || true)"

          if [ -n "$local_head" ] && [ "$local_head" = "$remote_head" ]; then
            log_info "${repo_name}: ${default_branch} already up to date"
            outcome="synced"
          elif git -C "$default_wt" merge --ff-only "origin/${default_branch}" >/dev/null 2>&1; then
            log_success "${repo_name}: ${default_branch} fast-forwarded to origin/${default_branch}"
            outcome="synced"
          else
            log_warning "${repo_name}: ${default_branch} diverged from origin/${default_branch} (local commits); skipping"
            outcome="skipped"
          fi
        fi
      fi
    fi

    if [ "$do_prune" = true ]; then
      git -C "$repo_path" worktree prune --expire=1.week.ago >/dev/null 2>&1 || true
    fi

    printf '%s\n' "$outcome" >"$status_file"
  } >"$log_file" 2>&1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repos-root)
      require_value "$@"
      repos_root="$2"
      shift 2
      ;;
    --jobs)
      require_value "$@"
      parallel_jobs="$2"
      shift 2
      ;;
    --no-prune)
      do_prune=false
      shift
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

if [ -n "$parallel_jobs" ]; then
  if ! [[ "$parallel_jobs" =~ ^[0-9]+$ ]] || [ "$parallel_jobs" -lt 1 ]; then
    log_error "--jobs must be a positive integer."
    exit 1
  fi
fi

repos_root="$(expand_home_path "$repos_root")"

if [ ! -d "$repos_root" ]; then
  log_error "Repos root does not exist: ${repos_root}"
  exit 1
fi

repos_root="$(cd "$repos_root" >/dev/null 2>&1 && pwd -P)"

repo_paths=()
repo_names=()

for repo_path in "$repos_root"/*/; do
  [ -d "$repo_path" ] || continue
  repo_name="$(basename "$repo_path")"

  if ! is_bare_container "$repo_path"; then
    continue
  fi

  repo_paths+=("$repo_path")
  repo_names+=("$repo_name")
done

if [ "${#repo_paths[@]}" -eq 0 ]; then
  log_info "No bare-container repos found under ${repos_root}"
  exit 0
fi

if [ -z "$parallel_jobs" ]; then
  parallel_jobs="$(default_parallel_jobs)"
fi

log_info "Syncing ${#repo_paths[@]} repo(s) with up to ${parallel_jobs} parallel jobs"

tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/git-workspace-sync.XXXXXX")"
trap 'rm -rf "$tmp_dir"' EXIT

pids=()
log_files=()
status_files=()

for i in "${!repo_paths[@]}"; do
  wait_for_available_slot "$parallel_jobs"

  log_file="${tmp_dir}/${i}.log"
  status_file="${tmp_dir}/${i}.status"

  sync_repo "${repo_paths[$i]}" "${repo_names[$i]}" "$log_file" "$status_file" &

  pids+=("$!")
  log_files+=("$log_file")
  status_files+=("$status_file")
done

for pid in "${pids[@]}"; do
  wait "$pid" || true
done

synced_count=0
skipped_count=0
failed_count=0

for i in "${!repo_paths[@]}"; do
  if [ -f "${log_files[$i]}" ]; then
    cat "${log_files[$i]}"
  fi

  if [ -f "${status_files[$i]}" ]; then
    result="$(cat "${status_files[$i]}")"
  else
    result="failed"
    log_warning "No result recorded for ${repo_names[$i]}"
  fi

  case "$result" in
    synced) synced_count=$((synced_count + 1)) ;;
    skipped) skipped_count=$((skipped_count + 1)) ;;
    *) failed_count=$((failed_count + 1)) ;;
  esac
done

printf '\n%s%sSummary%s\n' "${color_bold}" "${color_blue}" "${color_reset}"
printf 'Repos root:      %s\n' "$repos_root"
printf 'Repos synced:    %d\n' "$synced_count"
if [ "$skipped_count" -gt 0 ]; then
  printf 'Repos skipped:   %d\n' "$skipped_count"
fi
if [ "$failed_count" -gt 0 ]; then
  printf 'Repos failed:    %d\n' "$failed_count"
  exit 1
fi
