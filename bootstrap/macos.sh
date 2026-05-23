#!/bin/zsh
set -euo pipefail

APP_SUPPORT="$HOME/Library/Application Support/UsefulAIAgent"
REPO_DIR="$APP_SUPPORT/source/useful-ai-agent"
LOG_DIR="$HOME/Library/Logs/UsefulAIAgent"
BIN_DIR="$HOME/.local/bin"
REPO_URL="${USEFUL_AGENT_REPO_URL:-https://github.com/dperhar/useful-ai-agent.git}"

mkdir -p "$APP_SUPPORT/source" "$LOG_DIR" "$BIN_DIR"

echo "Useful AI Agent bootstrap"
echo "Repo: $REPO_URL"
echo "Runtime: $APP_SUPPORT"
echo

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv from official Astral installer..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Git is required for versioned context and encrypted backups."
  echo "Install Apple Command Line Tools when prompted, then re-run this script:"
  xcode-select --install || true
  exit 2
fi

if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"
uv tool install --force ./packages/useful-agent

echo
echo "Bootstrap installed useful-agent."
echo "Next: run useful-agent install --guided"
echo
exec useful-agent install --guided
