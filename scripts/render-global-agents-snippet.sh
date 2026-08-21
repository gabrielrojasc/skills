#!/usr/bin/env bash

set -euo pipefail

script_name="${0##*/}"
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
template="${script_dir}/../templates/GLOBAL.AGENTS.snippet.md"
repos_root='~/git'

usage() {
  cat <<EOF
Usage: ${script_name} [options]

Print the global AGENTS.md section to stdout. This script never writes or
merges the target file.

Options:
  --repos-root PATH  Repository containers root (default: ${repos_root})
  --template PATH    Alternate template
  -h, --help         Show this help
EOF
}

require_value() {
  if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
    printf 'error: %s requires a value\n' "$1" >&2
    exit 2
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repos-root)
      require_value "$@"
      repos_root="$2"
      shift 2
      ;;
    --template)
      require_value "$@"
      template="$2"
      shift 2
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      printf 'error: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ ! -f "$template" ]; then
  printf 'error: template not found: %s\n' "$template" >&2
  exit 1
fi

awk -v repos_root="$repos_root" '
  {
    while ((position = index($0, "<REPOS_ROOT>")) > 0) {
      $0 = substr($0, 1, position - 1) repos_root substr($0, position + 12)
    }
    print
  }
' "$template"
