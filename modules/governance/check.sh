#!/bin/zsh
set -euo pipefail

APP_SUPPORT="{{APP_SUPPORT}}"
WORKSPACE="{{WORKSPACE}}"

ok=1
check_file() {
  if [ -e "$1" ]; then
    echo "OK   $2"
  else
    echo "WARN $2 missing: $1"
    ok=0
  fi
}

echo "Useful AI Agent health"
echo "created_at=$(date '+%Y-%m-%d %H:%M:%S %Z')"
echo

command -v uv >/dev/null && echo "OK   uv" || { echo "WARN uv missing"; ok=0; }
command -v git >/dev/null && echo "OK   git" || { echo "WARN git missing"; ok=0; }

check_file "$WORKSPACE/AGENTS.md" "root AGENTS.md"
check_file "$WORKSPACE/CLAUDE.md" "CLAUDE.md wrapper"
check_file "$WORKSPACE/.cursor/rules/useful-agent-router.mdc" "Cursor router"
check_file "$APP_SUPPORT/nanobot/config.json" "Nanobot config"
check_file "$APP_SUPPORT/bin/run-nanobot.sh" "Nanobot launcher"
check_file "$APP_SUPPORT/runtime/venv/bin/mempalace" "MemPalace binary"
check_file "$HOME/Library/Application Support/Transcripted/captures" "Transcripted captures"
check_file "$APP_SUPPORT/backups" "backup vault"

if lsof -nP -iTCP:8765 -sTCP:LISTEN 2>/dev/null | grep -q '127.0.0.1:8765'; then
  echo "OK   WebSocket listens on 127.0.0.1:8765"
else
  echo "WARN WebSocket listener not found"
fi

exit $((1-ok))
