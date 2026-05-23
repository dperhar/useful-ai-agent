# Nanobot Module

Nanobot provides the always-on chat interface.

## Defaults

- Telegram is enabled only after a token and at least one allowed user id exist.
- WebSocket enabled on `127.0.0.1:8765` with a generated local secret.
- Default reasoning effort: `medium`.
- One-turn markers: `high`, `xhigh`, `/high`, `/xhigh`, `high -`, `xhigh -`.
- `/improve` expands to the installed improve workflow.
- Guest Mode uses final-only replies by default for desktop compatibility.

## Manual BotFather Setup

Enable only what you need:

- Groups: on for group chats.
- Group Privacy: on by default.
- Guest Chat Mode: on for mention-in-any-chat.
- Bot-to-bot: off unless you understand loop risks.

Add allowed Telegram user IDs before sharing the bot.

The installer applies runtime patches after `nanobot-ai` is installed and
stops before LaunchAgent start if patch markers are missing.
