# Troubleshooting

## `useful-agent` command not found

Restart Terminal or run:

```zsh
export PATH="$HOME/.local/bin:$PATH"
```

## Telegram bot does not reply

Run:

```zsh
useful-agent check
useful-agent logs
```

Verify the token was pasted correctly and your Telegram user is allowed.

## Guest Mode works on phone but not desktop

Some Telegram desktop clients can lag behind mobile Guest Mode support. Use
normal private/group bot chat or update Telegram. The harness defaults to
final-only guest replies for cross-client compatibility.

## Transcripted missing

Install it from the official source:

https://transcripted.app/

Then approve permissions and run `useful-agent check`.

## Disk grows quickly

Run health checks and inspect generated caches:

```zsh
useful-agent check
```

The harness should not run recurring temp guards. Disk cleanup should be tied to
backup/update/check operations.
