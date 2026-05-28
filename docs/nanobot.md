# Nanobot Module

Nanobot provides the always-on chat interface.

## Defaults

- Telegram is enabled only after a token and at least one allowed user id exist.
- WebSocket enabled on `127.0.0.1:8765` with a generated local secret.
- Default reasoning effort: `medium`.
- One-turn markers: `high`, `xhigh`, `/high`, `/xhigh`, `high -`, `xhigh -`.
- `/improve` expands to the installed improve workflow.
- `/goal` is preserved as a Codex-native command and routed to Codex, not
  reimplemented as a local pseudo-workflow.
- `/improve` and `/goal` are recognized as exact tokens anywhere in the
  message; `/improve@bot` and `/goal@bot` are intentionally not shortcuts.
- Guest Mode uses final-only replies by default for desktop compatibility.
- Image generation uses Nanobot's `generate_image` tool with provider
  `codex_cli`, which invokes Codex CLI `$imagegen` and sends generated PNGs
  through Telegram media.

## Manual BotFather Setup

Enable only what you need:

- Groups: on for group chats.
- Group Privacy: on by default.
- Guest Chat Mode: on for mention-in-any-chat.
- Bot-to-bot: off unless you understand loop risks.

Add allowed Telegram user IDs before sharing the bot.

The installer applies runtime patches after `nanobot-ai` is installed and
stops before LaunchAgent start if patch markers are missing.

## Image Generation

Requirements:

- `codex` CLI installed.
- `codex login` completed for the same macOS user running Nanobot.
- `CODEX_HOME` points to that user's `.codex` directory.

This path uses Codex/ChatGPT subscription usage limits. It does not require an
OpenAI API key and does not use OpenAI API billing.
