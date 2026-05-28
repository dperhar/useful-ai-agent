#!/bin/zsh
set -euo pipefail

if ! command -v useful-agent >/dev/null 2>&1; then
  echo "useful-agent command not found. Run bootstrap/macos.sh first." >&2
  exit 2
fi

exec useful-agent backup create
