# Harness Router

Read after the root `AGENTS.md` for tasks under `Harness/`.

## Scope

- Local runtime scripts and configs.
- Nanobot, Telegram, WebSocket, MemPalace, Transcripted, backups, health checks.
- Menu-bar app and desktop commands.

## Rules

- Redact secrets by default.
- Prefer dry-run/report behavior before mutation.
- Never delete backup vault contents.
- Do not expose local WebSocket beyond `127.0.0.1` unless the user explicitly enables advanced mode.
