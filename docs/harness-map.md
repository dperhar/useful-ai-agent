# Harness Map

Useful AI Agent is a set of cooperating local entities, not one prompt.

## Entities

- Agent apps: Codex, Cursor, Claude Code/Cowork, browser AI tools.
- Native terminal: zsh, Git, launchd, Keychain, local files.
- Router layer: `AGENTS.md`, scoped routers, `CLAUDE.md`, Cursor rules.
- Context layer: lifecycle-split markdown files, source-of-truth timelines, archive.
- Memory layer: MemPalace search, diary, KG, taxonomy, MCP tools.
- Chat layer: Nanobot, Telegram bot, local WebSocket on `127.0.0.1`.
- Meeting layer: Transcripted app, local captures, read-only MCP/folder fallback.
- Skills layer: setup, cleanup, improve, memory reconciliation, Telegram ops, backups, voice template.
- Backup layer: encrypted Git bundles, Keychain password, optional iCloud mirror.
- Governance layer: health checks, disk guard, update checks, redacted reports.
- UX layer: menu-bar app, desktop commands, local console, agent-led README.

## Default Flow

1. User gives GitHub URL to their agent.
2. Agent reads README and runs bootstrap.
3. Bootstrap installs runtime and creates workspace.
4. User creates Telegram bot token in BotFather.
5. Installer configures Nanobot, MemPalace, Transcripted, backups, routers, skills.
6. Menu bar and Telegram become the daily control surfaces.
7. Agents use the same files and memory rather than separate hidden contexts.
