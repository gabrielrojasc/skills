#!/usr/bin/env bash
# Download a repository at one commit into a new directory, without history.
#
#   fetch-source.sh <owner>/<repo> <sha> <dest>
#
# One tarball request through gh replaces an API call per file read, and gh
# supplies the credentials for private repositories.
set -euo pipefail
usage="usage: fetch-source.sh <owner>/<repo> <sha> <dest>"
repo="${1:?$usage}"
sha="${2:?$usage}"
dest="${3:?$usage}"
[[ "$repo" == */* ]] || { echo "error: expected <owner>/<repo>, got ${repo}" >&2; exit 2; }
[[ ! -e "$dest" ]] || { echo "error: ${dest} already exists" >&2; exit 2; }
archive="$(mktemp)"
trap 'rm -f "$archive"' EXIT
gh api "repos/${repo}/tarball/${sha}" > "$archive"
mkdir -p "$dest"
tar -xzf "$archive" -C "$dest" --strip-components 1 || { rm -rf "$dest"; exit 1; }
