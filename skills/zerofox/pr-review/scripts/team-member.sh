#!/usr/bin/env bash
# Print whether a GitHub user is on a team: member, not-member, or unknown.
#
#   team-member.sh <org>/<team> <login>
#
# The membership endpoint returns 404 when the token can't see memberships, so
# this reads the roster instead. A login missing from the roster means
# not-member only when the roster is complete: its length equals members_count.
set -euo pipefail
usage="usage: team-member.sh <org>/<team> <login>"
team="${1:?$usage}"
login="${2:?$usage}"
org="${team%%/*}"
slug="${team#*/}"
[[ "$org" != "$team" && -n "$slug" ]] || { echo "error: expected <org>/<team>, got ${team}" >&2; exit 2; }
logins="$(gh api "orgs/${org}/teams/${slug}/members" --paginate --jq '.[].login')" || { echo unknown; exit 0; }
if grep -qixF -- "$login" <<<"$logins"; then
  echo member
elif count="$(gh api "orgs/${org}/teams/${slug}" --jq .members_count)" &&
  [[ "$(grep -c . <<<"$logins" || true)" == "$count" ]]; then
  echo not-member
else
  echo unknown
fi
