# CLI Surface

`useful-agent` is the stable local control API.

```zsh
useful-agent install --guided
useful-agent check
useful-agent doctor --json
useful-agent configure project --guided
useful-agent configure project --project-root /path/to/project --install-root /path/to/project/Useful\ Agent
useful-agent configure telegram --guided
useful-agent configure websocket
useful-agent configure adapters --target /path/to/project
useful-agent menu install
useful-agent start
useful-agent stop
useful-agent restart
useful-agent backup
useful-agent backup list --limit 5
useful-agent backup restore --latest 1
useful-agent backup restore --file /path/to/project.root.bundle.enc
useful-agent backup mirror enable --path /path/to/encrypted-backups
useful-agent backup mirror disable
useful-agent backup mirror status
useful-agent backup open-folder
useful-agent open-project
useful-agent open-runtime
useful-agent logs
useful-agent update
useful-agent uninstall
```

The project root is the source-of-truth folder. The Useful Agent runtime folder
lives inside it, while encrypted backup artifacts live outside it. The menu bar
app shells out to this CLI. Agents should prefer this CLI instead of editing
LaunchAgents or configs directly.

`backup restore` is non-destructive. It restores into a separate folder and
prints the manual next step instead of replacing the active project.
