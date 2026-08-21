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

log_command() {
  printf '%s%srun%s %s\n' "${color_blue}" "${color_bold}" "${color_reset}" "$1"
}

self="$0"
repos_root="~/git"
repo_name=""
repo_url=""
manifest_file=""

usage() {
  cat <<EOF
Usage: ${script_name} [options] <repo-url>
       ${script_name} [options] --from-manifest <file>

Clone or repair one repo in the bare-container layout:
  <repos-root>/<repo>/.git
  <repos-root>/<repo>/<default-branch>

Options:
  --repos-root DIR     Repositories root (default: ${repos_root})
  --repo-name NAME     Directory name under repos root (default: derived from URL)
  --from-manifest FILE Add or repair many repos; one '<repo-url> [repo-name]' per line.
                       Blank lines, '#' comment lines, and trailing ' #' comments are ignored.
  -h, --help           Show this help
EOF
}

expand_home_path() {
  printf '%s' "${1/#\~/$HOME}"
}

require_value() {
  if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
    log_error "$1 requires a value."
    exit 2
  fi
}

redact_url() {
  local url="$1"

  case "$url" in
    https://*@*)
      printf 'https://<redacted>@%s' "${url#https://*@}"
      ;;
    http://*@*)
      printf 'http://<redacted>@%s' "${url#http://*@}"
      ;;
    *://*:*@*)
      scheme="${url%%://*}"
      rest="${url#*://}"
      printf '%s://<redacted>@%s' "$scheme" "${rest#*@}"
      ;;
    *)
      printf '%s' "$url"
      ;;
  esac
}

url_has_credentials() {
  local url="$1"

  case "$url" in
    https://*@* | http://*@* | *://*:*@*) return 0 ;;
    *) return 1 ;;
  esac
}

physical_path() {
  local path="$1"

  if [ ! -e "$path" ]; then
    return 1
  fi

  (
    cd "$path" >/dev/null 2>&1 &&
      pwd -P
  )
}

path_is_under() {
  local child="$1"
  local parent="$2"

  case "${child}/" in
    "${parent}/"*) return 0 ;;
    *) return 1 ;;
  esac
}

derive_repo_name() {
  local url="$1"
  local name=""

  name="${url##*/}"
  name="${name%%\?*}"
  name="${name%.git}"

  if [ -z "$name" ] || [ "$name" = "$url" ]; then
    name="${url##*:}"
    name="${name##*/}"
    name="${name%.git}"
  fi

  printf '%s' "$name"
}

resolve_default_branch() {
  local repo_path="$1"

  if git -C "$repo_path" remote set-head origin --auto >/dev/null 2>&1; then
    :
  else
    log_warning "Could not set origin/HEAD automatically; falling back to main/master detection"
  fi

  if git -C "$repo_path" symbolic-ref --short refs/remotes/origin/HEAD >/dev/null 2>&1; then
    git -C "$repo_path" symbolic-ref --short refs/remotes/origin/HEAD | sed 's@^origin/@@'
    return 0
  fi

  if git -C "$repo_path" rev-parse --verify refs/remotes/origin/main^{commit} >/dev/null 2>&1; then
    printf 'main'
    return 0
  fi

  if git -C "$repo_path" rev-parse --verify refs/remotes/origin/master^{commit} >/dev/null 2>&1; then
    printf 'master'
    return 0
  fi

  return 1
}

configure_bare_repo() {
  local repo_path="$1"

  if [ "$(git -C "$repo_path" rev-parse --is-bare-repository 2>/dev/null)" != "true" ]; then
    log_error "Expected a bare repo at ${repo_path}/.git."
    return 1
  fi

  git -C "$repo_path" config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
  git -C "$repo_path" fetch origin --quiet
}

configure_default_branch_tracking() {
  local repo_path="$1"
  local default_branch="$2"

  log_command "git -C ${repo_path} branch --set-upstream-to=origin/${default_branch} ${default_branch}"
  git -C "$repo_path" branch --set-upstream-to="origin/${default_branch}" "$default_branch" >/dev/null
}

ensure_default_worktree() {
  local repo_path="$1"
  local default_branch="$2"
  local default_path="${repo_path}/${default_branch}"

  if git -C "$repo_path" worktree list --porcelain | grep -Fqx "worktree ${default_path}"; then
    if [ -d "$default_path" ]; then
      configure_default_branch_tracking "$repo_path" "$default_branch"

      if [ -n "$(git -C "$default_path" status --porcelain 2>/dev/null)" ]; then
        log_error "Default worktree has local changes: ${default_path}"
        return 1
      fi

      log_command "git -C ${default_path} merge --ff-only origin/${default_branch}"
      if git -C "$default_path" merge --ff-only "origin/${default_branch}" >/dev/null; then
        log_info "Default worktree ready: ${default_path}"
        return 0
      fi

      log_error "Could not fast-forward default worktree: ${default_path}"
      return 1
    fi

    log_warning "Default worktree registration is stale; pruning: ${default_path}"
    git -C "$repo_path" worktree remove --force "$default_path" >/dev/null 2>&1 || true
    git -C "$repo_path" worktree prune
  fi

  if [ -e "$default_path" ]; then
    log_error "Default worktree path exists but is not registered: ${default_path}"
    return 1
  fi

  if ! git -C "$repo_path" show-ref --verify --quiet "refs/heads/${default_branch}"; then
    git -C "$repo_path" branch "$default_branch" "refs/remotes/origin/${default_branch}"
  elif git -C "$repo_path" merge-base --is-ancestor "refs/heads/${default_branch}" "refs/remotes/origin/${default_branch}" 2>/dev/null; then
    git -C "$repo_path" branch -f "$default_branch" "refs/remotes/origin/${default_branch}" >/dev/null
  else
    log_error "Local default branch cannot fast-forward to origin/${default_branch}."
    return 1
  fi

  configure_default_branch_tracking "$repo_path" "$default_branch"

  log_command "git -C ${repo_path} worktree add ${default_path} ${default_branch}"
  git -C "$repo_path" worktree add "$default_path" "$default_branch" >/dev/null
}

process_manifest() {
  local file="$1"
  local manifest_repos_root="$2"
  local total=0
  local ok=0
  local failed=0
  local line=""
  local url=""
  local name=""
  local rest=""

  while IFS= read -r line || [ -n "$line" ]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -n "$line" ] || continue
    case "$line" in
      \#*) continue ;;
    esac

    # Drop an inline comment (whitespace followed by '#') and re-trim.
    line="${line%%[[:space:]]#*}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -n "$line" ] || continue

    read -r url name rest <<<"$line"
    total=$((total + 1))

    if [ -n "$rest" ]; then
      printf '\n%s%s[%d] %s%s\n' "${color_bold}" "${color_blue}" "$total" "$(redact_url "$url")" "${color_reset}"
      log_error "Manifest entry [${total}] has too many fields; expected '<repo-url> [repo-name]'."
      failed=$((failed + 1))
      continue
    fi

    printf '\n%s%s[%d] %s%s\n' "${color_bold}" "${color_blue}" "$total" "$(redact_url "$url")" "${color_reset}"

    if [ -n "$name" ]; then
      if "$self" --repos-root "$manifest_repos_root" --repo-name "$name" "$url"; then
        ok=$((ok + 1))
      else
        failed=$((failed + 1))
      fi
    else
      if "$self" --repos-root "$manifest_repos_root" "$url"; then
        ok=$((ok + 1))
      else
        failed=$((failed + 1))
      fi
    fi
  done <"$file"

  printf '\n%s%sManifest summary%s\n' "${color_bold}" "${color_blue}" "${color_reset}"
  printf 'Repos processed: %d\n' "$total"
  printf 'Repos ready:     %d\n' "$ok"
  if [ "$failed" -gt 0 ]; then
    printf 'Repos failed:    %d\n' "$failed"
    return 1
  fi
  return 0
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repos-root)
      require_value "$@"
      repos_root="$2"
      shift 2
      ;;
    --repo-name)
      require_value "$@"
      repo_name="$2"
      shift 2
      ;;
    --from-manifest)
      require_value "$@"
      manifest_file="$2"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    -*)
      log_error "Unknown option: $1"
      usage >&2
      exit 2
      ;;
    *)
      if [ -z "$repo_url" ]; then
        repo_url="$1"
      else
        log_error "Unexpected argument: $1"
        usage >&2
        exit 2
      fi
      shift
      ;;
  esac
done

if [ -n "$manifest_file" ]; then
  if [ -n "$repo_url" ]; then
    log_error "Pass either a repo URL or --from-manifest, not both."
    exit 2
  fi
  if [ -n "$repo_name" ]; then
    log_error "--repo-name is not used with --from-manifest; set names per line in the manifest."
    exit 2
  fi
  if [ ! -f "$manifest_file" ]; then
    log_error "Manifest file not found: ${manifest_file}"
    exit 2
  fi

  if process_manifest "$manifest_file" "$repos_root"; then
    exit 0
  fi
  exit 1
fi

if [ -z "$repo_url" ]; then
  log_error "Repo URL is required."
  usage >&2
  exit 2
fi

if url_has_credentials "$repo_url"; then
  log_error "Repo URL contains embedded credentials; use a credential helper or a non-credentialed remote URL."
  exit 2
fi

if [ -z "$repo_name" ]; then
  repo_name="$(derive_repo_name "$repo_url")"
fi

if [ -z "$repo_name" ] || [ "$repo_name" = "." ] || [ "$repo_name" = ".." ] || [[ "$repo_name" == *"/"* ]]; then
  log_error "Could not derive a safe repo name from URL. Pass --repo-name."
  exit 2
fi

repos_root="$(expand_home_path "$repos_root")"
redacted_repo_url="$(redact_url "$repo_url")"
tmp_path=""

cleanup_tmp() {
  if [ -n "$tmp_path" ] && [ -d "$tmp_path" ]; then
    rm -rf "$tmp_path"
  fi
}

trap cleanup_tmp EXIT

mkdir -p "$repos_root"
repos_root="$(cd "$repos_root" && pwd -P)"
repo_path="${repos_root}/${repo_name}"

if [ -e "$repo_path" ]; then
  repo_real_path="$(physical_path "$repo_path")" || {
    log_error "Could not resolve destination path: ${repo_path}"
    exit 1
  }
  if ! path_is_under "$repo_real_path" "$repos_root"; then
    log_error "Destination resolves outside repos root: ${repo_path} -> ${repo_real_path}"
    exit 1
  fi

  if [ ! -d "${repo_path}/.git" ]; then
    log_error "Destination exists but is not a bare-container repo: ${repo_path}"
    exit 1
  fi

  current_origin="$(git -C "$repo_path" remote get-url origin 2>/dev/null || true)"
  if [ -z "$current_origin" ]; then
    log_command "git -C ${repo_path} remote add origin ${redacted_repo_url}"
    git -C "$repo_path" remote add origin "$repo_url"
  elif [ "$current_origin" != "$repo_url" ]; then
    log_error "Destination origin differs from requested URL: $(redact_url "$current_origin")"
    exit 1
  fi

  log_info "Repairing existing bare-container repo: ${repo_path}"
  configure_bare_repo "$repo_path"
  default_branch="$(resolve_default_branch "$repo_path")" || {
    log_error "Could not resolve default branch for ${repo_name}."
    exit 1
  }
  ensure_default_worktree "$repo_path" "$default_branch"
  log_success "Repo ready: ${repo_path}"
  exit 0
fi

if [ -e "${repos_root}/.${repo_name}.git-workspace-tmp" ]; then
  log_error "Temporary path already exists: ${repos_root}/.${repo_name}.git-workspace-tmp"
  exit 1
fi

tmp_path="${repos_root}/.${repo_name}.git-workspace-tmp"

log_command "git ls-remote ${redacted_repo_url} HEAD"
git ls-remote "$repo_url" HEAD >/dev/null

mkdir -p "$tmp_path"
log_command "git clone --bare ${redacted_repo_url} ${tmp_path}/.git"
git clone --bare "$repo_url" "${tmp_path}/.git" >/dev/null

git -C "$tmp_path" remote set-url origin "$repo_url"
configure_bare_repo "$tmp_path"
default_branch="$(resolve_default_branch "$tmp_path")" || {
  log_error "Could not resolve default branch for ${repo_name}."
  exit 1
}

log_command "mv ${tmp_path} ${repo_path}"
mv "$tmp_path" "$repo_path"
tmp_path=""

ensure_default_worktree "$repo_path" "$default_branch"
log_success "Repo ready: ${repo_path}"
