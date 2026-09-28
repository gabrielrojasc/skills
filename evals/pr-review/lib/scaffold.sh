#!/usr/bin/env bash
# Prepare a run workspace: copy one fixture PR and put the fake gh on bin/.
set -euo pipefail
fixture="${1:?fixture name required}"
lib="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
cp -R "${lib}/../fixtures/${fixture}" fixtures
mkdir -p bin
cp "${lib}/fake-gh.py" bin/gh
chmod +x bin/gh
