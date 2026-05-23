---
name: telegram-agent-ops
description: Operate Nanobot Telegram agent, WebSocket, Guest Mode, effort markers, and health checks safely.
---

# Telegram Agent Ops

Use this for Nanobot/Telegram setup and debugging.

Checklist:

- Verify Telegram token exists but never print it.
- Verify allowed users are configured before sharing bot.
- Keep WebSocket on `127.0.0.1`.
- Default effort is `medium`; one-turn markers are `high` and `xhigh`.
- Guest Mode uses final-only replies unless client compatibility is verified.
- Check logs with redaction before changing config.
