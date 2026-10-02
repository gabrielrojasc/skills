#!/usr/bin/env bash
# Print a Markdown link to each line in a PR's Files changed view.
#
#   file-links.sh <owner>/<repo> <pr-number> <path>:<line>...
#
# GitHub anchors each file with the SHA-256 of its path, followed directly by
# R<line> for a line on the new side.
set -euo pipefail
repo="${1:?usage: file-links.sh <owner>/<repo> <pr-number> <path>:<line>...}"
pr="${2:?usage: file-links.sh <owner>/<repo> <pr-number> <path>:<line>...}"
shift 2
for ref in "$@"; do
  path="${ref%:*}"
  line="${ref##*:}"
  [[ "$path" != "$ref" && "$line" =~ ^[0-9]+$ ]] || { echo "error: expected <path>:<line>, got ${ref}" >&2; exit 2; }
  hash="$(printf '%s' "$path" | shasum -a 256 | cut -d' ' -f1)"
  printf '[%s](https://github.com/%s/pull/%s/files#diff-%sR%s)\n' "$ref" "$repo" "$pr" "$hash" "$line"
done
