# Backup Module

Backups are encrypted Git bundles.

## Defaults

- Workspace is versioned with Git.
- Backup password is stored in macOS Keychain.
- Encrypted artifacts live outside the workspace.
- iCloud mirror is enabled by default when iCloud Drive exists.
- Mirror location is configurable and can be any writable folder.
- Historical backups should not be deleted by agents.

## Commands

```zsh
useful-agent backup
useful-agent backup list --limit 5
useful-agent backup list --json --limit 5
useful-agent backup restore --latest 1
useful-agent backup restore --file /path/to/workspace.bundle.enc
useful-agent backup mirror status
useful-agent backup mirror enable --path "$HOME/Library/Mobile Documents/com~apple~CloudDocs/UsefulAIAgentBackups"
useful-agent backup mirror disable
useful-agent backup open-folder
```

## Mirror

The mirror stores encrypted artifacts and manifests only. By default the
installer suggests:

```text
~/Library/Mobile Documents/com~apple~CloudDocs/UsefulAIAgentBackups
```

The user can change or disable this from the menu bar. Agents must not hardcode
the mirror path; read it from `useful-agent backup mirror status`.

## Restore

Restore is explicit and writes to a new folder. It must never overwrite the
active workspace without user confirmation.

`restore --latest N` uses the currently configured backup search order:

1. Enabled mirror folder, if configured.
2. Local app backup vault.

After restore, inspect the new folder manually before replacing anything in the
active workspace.
