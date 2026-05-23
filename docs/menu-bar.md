# Menu Bar UX

The menu bar app is the nontechnical control surface.

## Required Actions

- Start harness.
- Stop harness.
- Restart harness.
- Run health check.
- Run encrypted backup.
- Open Telegram bot.
- Show local health. `127.0.0.1:8765` is a WebSocket endpoint, not a browser UI.
- View logs.
- Update runtime.
- Re-run onboarding.

The app must not store secrets. It calls `useful-agent` commands and displays
redacted output.

Current alpha install is an unsigned local build:

```zsh
useful-agent menu install
```

Signed/notarized distribution is on the product roadmap.
