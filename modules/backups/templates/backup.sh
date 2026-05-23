#!/bin/zsh
set -euo pipefail

WORKSPACE="{{WORKSPACE}}"
VAULT="{{VAULT}}"
SERVICE="{{SERVICE}}"
ACCOUNT="{{ACCOUNT}}"
TS="$(date '+%Y%m%d-%H%M%S')"
mkdir -p "$VAULT"

pass="$(security find-generic-password -w -s "$SERVICE" -a "$ACCOUNT" 2>/dev/null || true)"
if [ -z "$pass" ]; then
  echo "Set backup password:"
  read -rs "pass?Backup encryption password: "
  echo
  security add-generic-password -U -s "$SERVICE" -a "$ACCOUNT" -w "$pass"
fi

tmp="$(mktemp -d "${TMPDIR:-/tmp}/useful-agent-backup.XXXXXX")"
trap 'rm -rf "$tmp"' EXIT

cd "$WORKSPACE"
if [ ! -d .git ]; then
  git init
  git config user.name "Useful AI Agent Backup"
  git config user.email "useful-agent-backup@local"
fi

git add -A
git commit -m "Useful Agent backup snapshot $TS" >/dev/null 2>&1 || true
git bundle create "$tmp/workspace.bundle" HEAD

printf '%s' "$pass" | openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 \
  -pass stdin -in "$tmp/workspace.bundle" -out "$VAULT/workspace-$TS.bundle.enc"

chmod 600 "$VAULT/workspace-$TS.bundle.enc"
ln -sf "$VAULT/workspace-$TS.bundle.enc" "$VAULT/workspace-latest.bundle.enc"
echo "Encrypted backup: $VAULT/workspace-$TS.bundle.enc"
