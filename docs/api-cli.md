# CLI Surface

`useful-agent` is the stable local control API.

```zsh
useful-agent install --guided
useful-agent check
useful-agent start
useful-agent stop
useful-agent restart
useful-agent backup
useful-agent logs
useful-agent update
useful-agent uninstall
```

The menu bar app shells out to this CLI. Agents should prefer this CLI instead
of editing LaunchAgents or configs directly.
