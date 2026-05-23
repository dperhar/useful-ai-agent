# Nanobot Compatibility Patches

These are the behaviors the harness applies or verifies when upstream Nanobot
does not support them natively yet.

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
- final replies are sent with Bot API `answerGuestQuery`;
- streaming placeholder mode is opt-in only after client compatibility check.

Default is `final_only` because some desktop clients can show the initial guest
message but fail to repaint inline edits.
