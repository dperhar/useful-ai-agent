# Useful AI Agent

Plug-and-play local AI-agent harness for macOS.

This repo is designed for a non-technical user to give to their coding agent
in Codex, Cursor, Claude Code, or another local agent:

```text
Install this harness on my Mac:
https://github.com/dperhar/useful-ai-agent

Read README.md first. Run only official-source installers. Guide me through
manual steps such as creating a Telegram bot token. Do not print secrets.
After install, run useful-agent check and fix anything red.
```

## What You Get

- Router-first context architecture with `AGENTS.md`, scoped routers,
  `CLAUDE.md`, and Cursor rules.
- Local markdown source of truth plus MemPalace retrieval/write memory.
- Nanobot Telegram agent with local WebSocket on `127.0.0.1`.
- Transcripted meeting/dictation context through read-only MCP.
- Skills for setup, cleanup, `/improve`, memory reconciliation, Telegram ops,
  backups, and voice/style customization.
- Encrypted local Git bundle backups with Keychain password and optional iCloud
  mirror.
- Health checks and redacted reports.
- Native macOS menu-bar controller source for start/check/backup/update/logs.

See [docs/harness-map.md](docs/harness-map.md) for the full entity map.

## Install

The default install is native-first. Docker is optional and not required.

1. Ask your agent to inspect this repo.
2. Run the macOS bootstrap:

```zsh
curl -fsSL https://raw.githubusercontent.com/dperhar/useful-ai-agent/main/bootstrap/macos.sh -o /tmp/useful-agent-bootstrap.sh
less /tmp/useful-agent-bootstrap.sh
zsh /tmp/useful-agent-bootstrap.sh
```

3. Follow the guided steps:

- Create a Telegram bot in BotFather.
- Paste the bot token when prompted.
- Approve macOS permissions requested by Transcripted and the menu app.
- Run `useful-agent check`.

If the Mac does not yet have Python, the bootstrap installs `uv` from the
official Astral installer and lets `uv` manage Python.

## After Install

Use either:

- Telegram bot for daily chat.
- `http://127.0.0.1:8765` or local WebSocket clients for local integrations.
- Menu-bar app for start/stop/check/backup/update/logs.
- `useful-agent` CLI for agent-driven maintenance.

Common commands:

```zsh
useful-agent check
useful-agent start
useful-agent backup
useful-agent logs
useful-agent update
```

## Official Sources

The installer only uses allowlisted official sources. See
[docs/source-allowlist.md](docs/source-allowlist.md).

## Security Model

- Secrets go to macOS Keychain or local app configs, not into Git.
- Backups are encrypted before leaving the workspace.
- Transcripted context is read-only.
- WebSocket is local-only by default.
- Cloud LLM apps may still receive whatever context you explicitly send them.

See [docs/security-privacy.md](docs/security-privacy.md).

## Existing Toolkit Files

This repo also includes the original context-architecture reference files:

- [Context Architecture.md](Context%20Architecture.md)
- [Claude Code Prompt Patch.md](Claude%20Code%20Prompt%20Patch.md)
- [context-architecture-setup/SKILL.md](context-architecture-setup/SKILL.md)
- [context-architecture-cleanup/SKILL.md](context-architecture-cleanup/SKILL.md)
- [improve/SKILL.md](improve/SKILL.md)
