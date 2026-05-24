# Nanobot Compatibility Patches

These are the behaviors the harness applies and verifies when upstream Nanobot
does not support them natively yet. The installer runs scripts in
`modules/nanobot/patches/` after `nanobot-ai` is installed and refuses to start
the LaunchAgent if patch markers are missing.

## One-Turn Effort Markers

Supported markers anywhere in the user message:

- `high`
- `xhigh`
- `/high`
- `/xhigh`
- `high -`
- `xhigh -`
- `[effort=high]`
- `[effort=xhigh]`

The marker is stripped before the message is stored in chat history. Effort
resets to the configured default after one response.

## `/improve`

`/improve ...` expands to a normal request that triggers the installed
`improve` skill. The skill must critique, improve, and propose source
reconciliation.

## Telegram Guest Mode

Until the Telegram library exposes Guest Mode directly, the harness expects:

- polling includes `guest_message`;
- guest updates are read from raw update kwargs;
- guest queries are answered immediately with a placeholder;
- final replies edit the created inline guest message when the agent finishes;
- empty/progress outbound events must never consume the one allowed guest answer.

Default is `placeholder` because Telegram guest queries expire quickly. Long
tool calls cannot reliably wait for a final-only answer.

## Telegram Quote Replies

Telegram selected quote replies arrive as `message.quote` / raw
`api_kwargs["quote"]`, not as `reply_to_message.text`. The quote patch sends
the selected fragment to the agent as `[Quote from bot: ...]`. If no quote is
present, it falls back to the full replied message.

## Chat Hardening

`patch_nanobot_chat_hardening.py` fixes three Telegram runtime edge cases:

- Routes `/high`, `/xhigh`, `/improve`, `/effort`, and `/think` even when
  Telegram sends group commands as `/cmd@bot_username`.
- Debounces photo/video albums/media groups for 15 seconds and resets the timer on every
  incoming album item, reducing accidental split requests.
- On Telegram HTML parse fallback, sends stripped plain text instead of raw
  Markdown, so users do not see `**bold**` markers.

## Codex Error Diagnostics

`patch_nanobot_codex_errors.py` prevents empty user-facing errors like
`Error calling Codex:`. If the upstream exception has no message, the bot now
returns the exception class and logs a full traceback in the runtime logs.
