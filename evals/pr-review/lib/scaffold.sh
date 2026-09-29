#!/usr/bin/env bash
# Prepare a run workspace: copy each fixture PR into fixtures/<number>/ and put
# the fake gh on bin/.
set -euo pipefail
[[ $# -gt 0 ]] || { echo "usage: scaffold.sh <fixture>..." >&2; exit 2; }
lib="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
mkdir -p fixtures bin
for fixture in "$@"; do
  src="${lib}/../fixtures/${fixture}"
  number="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["number"])' "${src}/pr.json")"
  cp -R "$src" "fixtures/${number}"
done
cp "${lib}/fake-gh.py" bin/gh
chmod +x bin/gh
