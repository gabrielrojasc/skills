#!/usr/bin/env bash

set -euo pipefail

script_name="${0##*/}"
input=''
output=''
allow_fetch=false
chrome_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

usage() {
  cat <<EOF
Usage: ${script_name} --input FILE [options]

Render one Mermaid source file to PNG.

Options:
  --input FILE       Mermaid source file
  --output FILE      PNG destination; defaults to a temporary file
  --allow-fetch      Use npx when Mermaid CLI is not installed
  --chrome PATH      Chrome executable (default: ${chrome_path})
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
    --input)
      require_value "$@"
      input="$2"
      shift 2
      ;;
    --output)
      require_value "$@"
      output="$2"
      shift 2
      ;;
    --allow-fetch)
      allow_fetch=true
      shift
      ;;
    --chrome)
      require_value "$@"
      chrome_path="$2"
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

if [ -z "$input" ]; then
  printf 'error: --input is required\n' >&2
  exit 2
fi

if [ ! -f "$input" ]; then
  printf 'error: input not found: %s\n' "$input" >&2
  exit 1
fi

if [ ! -x "$chrome_path" ]; then
  printf 'error: Chrome executable not found: %s\n' "$chrome_path" >&2
  exit 1
fi

if [ -z "$output" ]; then
  output_dir="$(mktemp -d "${TMPDIR:-/tmp}/mermaid-validation.XXXXXX")"
  output="${output_dir}/diagram.png"
elif [ ! -d "$(dirname -- "$output")" ]; then
  printf 'error: output directory not found: %s\n' "$(dirname -- "$output")" >&2
  exit 1
fi

if [ -x './node_modules/.bin/mmdc' ]; then
  command_path=('./node_modules/.bin/mmdc')
elif command -v mmdc >/dev/null 2>&1; then
  command_path=('mmdc')
elif [ "$allow_fetch" = true ]; then
  command_path=('npx' '--yes' '-p' '@mermaid-js/mermaid-cli' 'mmdc')
else
  printf 'error: Mermaid CLI not found; install it locally or rerun with --allow-fetch\n' >&2
  exit 1
fi

PUPPETEER_EXECUTABLE_PATH="$chrome_path" "${command_path[@]}" \
  --input "$input" \
  --output "$output"

printf '%s\n' "$output"
