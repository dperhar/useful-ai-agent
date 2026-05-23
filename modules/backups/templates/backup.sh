#!/bin/zsh
set -euo pipefail

WORKSPACE="{{WORKSPACE}}"
VAULT="{{VAULT}}"
SERVICE="{{SERVICE}}"
ACCOUNT="{{ACCOUNT}}"
TS="$(date '+%Y%m%d-%H%M%S')"
REPORT="$VAULT/backup-$TS.report.txt"
mkdir -p "$VAULT"

pass="${USEFUL_AGENT_BACKUP_PASSWORD:-}"
if [ -z "$pass" ]; then
  pass="$(security find-generic-password -w -s "$SERVICE" -a "$ACCOUNT" 2>/dev/null || true)"
fi
if [ -z "$pass" ]; then
  echo "Set backup password. It is stored in macOS Keychain, not in repo/logs."
  read -rs "pass?Backup encryption password: "
  echo
  read -rs "confirm?Confirm backup encryption password: "
  echo
  if [ "$pass" != "$confirm" ]; then
    echo "Passwords do not match." >&2
    exit 2
  fi
  security add-generic-password -U -s "$SERVICE" -a "$ACCOUNT" -w "$pass"
fi

tmp="$(mktemp -d "${TMPDIR:-/tmp}/useful-agent-backup.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

cd "$WORKSPACE"
if [ ! -d .git ]; then
  git init
fi
git config user.name "Useful AI Agent Backup"
git config user.email "useful-agent-backup@local"

git add -A
if git diff --cached --quiet && git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "No staged changes; bundling current HEAD." > "$REPORT"
else
  git commit --allow-empty -m "Useful Agent backup snapshot $TS" >/dev/null
  echo "Committed backup snapshot $TS." > "$REPORT"
fi

git bundle create "$tmp/workspace.bundle" HEAD >> "$REPORT" 2>&1
printf '%s' "$pass" | openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 \
  -pass stdin -in "$tmp/workspace.bundle" -out "$tmp/workspace.bundle.enc"

printf '%s' "$pass" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 \
  -pass stdin -in "$tmp/workspace.bundle.enc" -out "$tmp/verify.bundle"
git bundle verify "$tmp/verify.bundle" >> "$REPORT" 2>&1
git clone "$tmp/verify.bundle" "$tmp/restore" >> "$REPORT" 2>&1
git -C "$tmp/restore" status --short >> "$REPORT" 2>&1

artifact="$VAULT/workspace-$TS.bundle.enc"
cp "$tmp/workspace.bundle.enc" "$artifact"
chmod 600 "$artifact"
chflags uchg "$artifact" 2>/dev/null || true
ln -sfn "$artifact" "$VAULT/workspace-latest.bundle.enc"

icloud="$HOME/Library/Mobile Documents/com~apple~CloudDocs/UsefulAIAgentBackups"
if [ -d "$HOME/Library/Mobile Documents/com~apple~CloudDocs" ]; then
  if mkdir -p "$icloud" 2>/dev/null && cp "$artifact" "$icloud/" 2>/dev/null; then
    chmod 600 "$icloud/$(basename "$artifact")" 2>/dev/null || true
    echo "iCloud mirror: $icloud/$(basename "$artifact")" >> "$REPORT"
  else
    echo "iCloud mirror skipped: iCloud folder exists but is not writable from this process." >> "$REPORT"
  fi
else
  echo "iCloud mirror skipped: iCloud Drive path not found." >> "$REPORT"
fi

echo "Encrypted backup verified: $artifact" >> "$REPORT"
echo "Encrypted backup verified: $artifact"
