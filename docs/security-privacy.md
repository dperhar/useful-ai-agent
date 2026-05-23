# Security And Privacy

## Local By Default

- Markdown workspace files stay on the Mac.
- MemPalace runs locally.
- Transcripted captures are local files.
- Backups are encrypted before optional iCloud mirroring.
- WebSocket binds to `127.0.0.1` by default.

## Cloud Boundary

Codex, Cursor, Claude, OpenAI, Anthropic, and other cloud model providers may
see the prompt/context sent to them by the user or by an agent app. This harness
reduces accidental context sprawl; it does not make cloud LLM calls private.

## Secrets

Secrets must be stored in macOS Keychain or app-native secure storage:

- Telegram bot token
- Backup encryption password
- OAuth/API credentials
- WebSocket token

Secrets must never be committed to Git, printed in logs, pasted into issues, or
included in health reports.

## Agent Safety Rules

- Never delete user files permanently.
- Never delete or weaken backup vaults.
- Never expose WebSocket to LAN without explicit user approval.
- Never install from non-allowlisted sources without explicit approval.
