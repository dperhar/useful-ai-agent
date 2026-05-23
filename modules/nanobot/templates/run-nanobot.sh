#!/bin/zsh
set -euo pipefail

APP_SUPPORT="{{APP_SUPPORT}}"
WORKSPACE="{{WORKSPACE}}"
NANOBOT="{{NANOBOT}}"
CONFIG="$APP_SUPPORT/nanobot/config.json"
LOG_DIR="$HOME/Library/Logs/UsefulAIAgent"

mkdir -p "$LOG_DIR"
cd "$WORKSPACE"

exec "$NANOBOT" gateway --config "$CONFIG" >> "$LOG_DIR/nanobot.log" 2>&1
