# Backup Module

Backups are encrypted Git bundle sets. There is one backup engine for both
small client projects and large personal/company projects with nested git repos.

## Defaults

- The selected project root is snapshotted with Git without mutating the source
  working tree.
- Backup password is stored in macOS Keychain.
- Encrypted artifacts live outside the project.
- iCloud mirror is enabled by default when iCloud Drive exists.
- Mirror location is configurable and can be any writable folder.
- Historical backups should not be deleted by agents.
- Backup-only excludes skip local models, build outputs, caches, logs, and
  runtime folders. Markdown, docs, presentations, and media stay included unless
  explicitly excluded.
- Nested git repositories are snapshotted as separate encrypted bundles by
  default, with a policy file for `snapshot` or `skip`.

## Commands

```zsh
useful-agent backup
useful-agent backup list --limit 5
useful-agent backup list --json --limit 5
useful-agent backup restore --latest 1
useful-agent backup restore --file /path/to/project.bundle.enc
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
active project without user confirmation.

`restore --latest N` uses the currently configured backup search order:

1. Enabled mirror folder, if configured.
2. Local app backup vault.

After restore, inspect the new folder manually before replacing anything in the
active project.

## Policy Files

Policy files live inside the project-local runtime:

```text
<install-root>/config/backups/backup-excludes.txt
<install-root>/config/backups/backup-nested-repos.txt
```

They are backup policy, not `.gitignore`.
