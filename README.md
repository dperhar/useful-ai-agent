# Useful AI Agent

Plug-and-play local AI-agent harness for macOS.

Status: alpha, self-diagnosing. The installer, doctor, menu bar, backups,
Telegram, and memory plumbing are implemented, but a clean-machine proof is
still a release gate before calling this enterprise-ready.

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
- Subscription-backed image generation through Codex CLI `$imagegen`, delivered
  back to Telegram as Nanobot media.
- Transcripted meeting/dictation context through read-only MCP.
- Skills for setup, cleanup, `/improve`, memory reconciliation, Telegram ops,
  backups, and voice/style customization.
- Encrypted local Git bundle backups with Keychain password, default iCloud
  mirror when available, and menu/CLI restore into a safe separate folder.
- Health checks and redacted reports.
- Native macOS menu-bar controller source for start/check/backup/update/logs.
- Project-local runtime: the installer asks for the main project folder and
  creates the Useful Agent runtime inside it instead of using a disconnected
  home-folder workspace.

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
- Paste at least one allowed Telegram user id when prompted.
- Install and log in to Codex CLI if you want image generation via subscription
  limits instead of OpenAI API billing.
- Approve macOS permissions requested by Transcripted and the menu app.
- Run `useful-agent doctor`.

If the Mac does not yet have Python, the bootstrap installs `uv` from the
official Astral installer and lets `uv` manage Python.

## After Install

Use either:

- Telegram bot for daily chat.
- Local WebSocket clients against `127.0.0.1:8765`. This is not a browser UI.
- Menu-bar app for start/stop/check/backup/update/logs.
- `useful-agent` CLI for agent-driven maintenance.

Common commands:

```zsh
useful-agent check
useful-agent doctor --json
useful-agent configure project --guided
useful-agent configure telegram --guided
useful-agent configure websocket
useful-agent menu install
useful-agent start
useful-agent backup
useful-agent backup list --limit 5
useful-agent backup restore --latest 1
useful-agent backup mirror status
useful-agent logs
useful-agent update
```

Restore is safe-by-default: it creates a separate restore folder and never
overwrites the active project.

## Workspace Model

Useful Agent separates four things:

- Project root: your real files and source-of-truth markdown.
- Runtime install root: a project-local `Useful Agent` folder, or
  `Harness/useful-agent-runtime` when the project already has a `Harness/`.
- Scratch workspace: agent runtime notes and control files inside the runtime.
- Backup vault: encrypted artifacts outside the project, with optional iCloud
  or custom-folder mirror.

Nanobot must work on the project root directly. It must not duplicate the
project into its own workspace.

When the user asks to save/remember/record context, the bot writes both:

- local memory for retrieval;
- the routed source-of-truth `.md` file, append-only.

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
