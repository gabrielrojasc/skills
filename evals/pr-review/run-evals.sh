#!/usr/bin/env bash
# Run `claude plugin eval` for this harness.
#
# Bash-granting evals refuse to start while ~/.aws/config has a
# credential_process or credential_source line, because the sandbox can't wall
# off what those commands read. This script comments those lines out for the
# duration of the run and restores the original file byte for byte on exit,
# including on failure or interrupt.
set -euo pipefail

here="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
aws_config="${HOME}/.aws/config"
backup=""

restore() {
  if [[ -n "$backup" && -f "$backup" ]]; then
    cp -p "$backup" "$aws_config"
    if cmp -s "$backup" "$aws_config"; then
      rm -f "$backup"
      echo "restored ${aws_config}" >&2
    else
      echo "error: ${aws_config} differs from its backup; backup kept at ${backup}" >&2
      exit 1
    fi
  fi
}
trap restore EXIT INT TERM

if [[ -f "$aws_config" ]] && grep -Eq '^[[:space:]]*(credential_process|credential_source)[[:space:]]*=' "$aws_config"; then
  backup="$(mktemp "${TMPDIR:-/tmp}/aws-config.XXXXXX")"
  cp -p "$aws_config" "$backup"
  sed -E 's/^([[:space:]]*)(credential_process|credential_source)([[:space:]]*=)/\1# eval-disabled \2\3/' \
    "$backup" > "$aws_config"
  echo "temporarily disabled credential_process lines in ${aws_config}" >&2
fi

cd "$here"
# The fake gh lives in each run's workspace bin/, which a relative PATH entry
# resolves against the run's working directory.
PATH="bin:${PATH}" claude plugin eval . --no-publish --trust-plugin --scaffold --allow-tools Bash Write Edit "$@"
