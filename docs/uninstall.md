# Uninstall

This intentionally does not delete your workspace or backups automatically.

```zsh
launchctl bootout "gui/$(id -u)/com.usefulaiagent.nanobot" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.usefulaiagent.nanobot.plist"
uv tool uninstall useful-agent 2>/dev/null || true
```

Manual review before deletion:

- `~/Useful AI Agent Workspace`
- `~/Library/Application Support/UsefulAIAgent`
- `~/Library/Logs/UsefulAIAgent`
- encrypted backup mirrors in iCloud
