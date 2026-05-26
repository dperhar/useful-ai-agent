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

## Guest Placeholder Custom Emoji

`patch_nanobot_custom_emoji.py` adds `/emoji_id` for extracting and persisting
Telegram `custom_emoji_id` values. Send `/emoji_id <custom emoji>` to the bot;
it saves the first custom emoji entity and uses it for the Guest Mode
placeholder marker.

Default placeholder carrier:

```text
⚡
```

After `/emoji_id <custom emoji>` is configured, Telegram renders the saved
custom emoji over that carrier, so the visible placeholder is only the custom
emoji.

## Codex CLI Image Generation

`patch_nanobot_codex_image_generation.py` adds a `codex_cli` provider to
Nanobot's built-in `generate_image` tool.

Why this exists:

- Codex CLI has subscription-backed image generation through `$imagegen`.
- Nanobot's upstream image tool expects API-key providers such as OpenRouter or
  AIHubMix.
- The harness bridges those two surfaces without exposing OpenAI API billing.

Runtime behavior:

- `tools.imageGeneration.provider = "codex_cli"`.
- The tool invokes `codex exec` with `$imagegen`.
- Codex writes the PNG under `CODEX_HOME/generated_images`.
- The patch converts the PNG into Nanobot's artifact format.
- Telegram receives the final image through Nanobot's normal media pipeline.

Requirements:

- `codex` CLI must be installed and logged in on the same macOS user account.
- The runtime must have access to `CODEX_HOME`.
- This uses Codex/ChatGPT subscription usage limits, not OpenAI API billing.

## Streamed Media Delivery

`patch_nanobot_streamed_media_delivery.py` fixes a delivery bug in streamed
Telegram turns.

Why this exists:

- Nanobot streams text through `_stream_delta` / `_stream_end`.
- Generated images are attached only to the final outbound message.
- Upstream `ChannelManager` skips final `_streamed` messages to avoid duplicate
  text, which also drops the attached image.

Runtime behavior:

- If a final `_streamed` outbound contains media, the patch sends a media-only
  Telegram message.
- The already-streamed text is not duplicated.
- This keeps immediate feedback/streaming and still delivers generated images.
