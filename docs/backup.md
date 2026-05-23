# Backup Module

Backups are encrypted Git bundles.

## Defaults

- Workspace is versioned with Git.
- Backup password is stored in macOS Keychain.
- Encrypted artifacts live outside the workspace.
- Optional iCloud mirror stores only encrypted files.
- Historical backups should not be deleted by agents.

## Restore

Restore is explicit and writes to a new folder. It must never overwrite the
active workspace without user confirmation.
