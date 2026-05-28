# CLI Surface

`useful-agent` is the stable local control API.

```zsh
useful-agent install --guided
useful-agent check
useful-agent doctor --json
useful-agent configure telegram --guided
useful-agent configure websocket
useful-agent configure adapters --target "$HOME/Useful AI Agent Workspace"
useful-agent menu install
useful-agent start
useful-agent stop
useful-agent restart
useful-agent backup
useful-agent backup list --limit 5
useful-agent backup restore --latest 1
useful-agent backup restore --file /path/to/workspace.bundle.enc
useful-agent backup mirror enable --path /path/to/encrypted-backups
useful-agent backup mirror disable
useful-agent backup mirror status
useful-agent backup open-folder
useful-agent logs
useful-agent update
useful-agent uninstall
```

`check` and `doctor` are read-only. They report missing state without creating
folders or writing config. The menu bar app shells out to this CLI. Agents
should prefer this CLI instead of editing LaunchAgents or configs directly.

`backup restore` is non-destructive. It restores into a separate folder and
prints the manual next step instead of replacing the active workspace.
