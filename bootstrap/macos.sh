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
UV_BIN="$(command -v uv || true)"
if [ -z "$UV_BIN" ] && [ -x "$HOME/.local/bin/uv" ]; then
  UV_BIN="$HOME/.local/bin/uv"
fi
if [ -z "$UV_BIN" ] && [ -x "/opt/homebrew/bin/uv" ]; then
  UV_BIN="/opt/homebrew/bin/uv"
fi
if [ -z "$UV_BIN" ]; then
  echo "uv install did not produce a usable binary. Add uv to PATH and re-run." >&2
  exit 2
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
printf '%s\n' "$REPO_DIR" > "$APP_SUPPORT/source-dir"
export USEFUL_AGENT_SOURCE_DIR="$REPO_DIR"
"$UV_BIN" tool install --force ./packages/useful-agent

USEFUL_AGENT_BIN="$(command -v useful-agent || true)"
if [ -z "$USEFUL_AGENT_BIN" ] && [ -x "$HOME/.local/bin/useful-agent" ]; then
  USEFUL_AGENT_BIN="$HOME/.local/bin/useful-agent"
fi
if [ -z "$USEFUL_AGENT_BIN" ]; then
  echo "useful-agent installed, but command is not on PATH. Try: $HOME/.local/bin/useful-agent install --guided" >&2
  exit 2
fi

echo
echo "Bootstrap installed useful-agent."
echo "Next: run useful-agent install --guided"
echo
exec "$USEFUL_AGENT_BIN" install --guided
