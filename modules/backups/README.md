# Backups Module

Provides encrypted, local-first backups.

Implementation:

- Git versioning for the workspace.
- Git bundle creation.
- AES-256-CBC encryption with PBKDF2.
- Password in macOS Keychain.
- Backup artifacts outside workspace.
- Optional iCloud mirror in future versions.

Agents may trigger backups but must not delete historical backup artifacts.
