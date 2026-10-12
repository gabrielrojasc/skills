#!/usr/bin/env bash
exec "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)/../../lib/scaffold.sh" widgets-py feature/eng-321-retry-webhooks
