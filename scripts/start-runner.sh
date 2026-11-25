#!/usr/bin/env bash
# Start the factory runner on the Mac (Basic B). Keep this terminal open.
# n8n in Docker reaches it at http://host.docker.internal:8787.
set -euo pipefail
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
if lsof -iTCP:8787 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 8787 is already in use:" >&2
  lsof -iTCP:8787 -sTCP:LISTEN >&2
  exit 1
fi
cd "$ROOT"
git pull -q --ff-only || echo "warning: git pull failed, running the local version" >&2
exec python3 runner/main.py
