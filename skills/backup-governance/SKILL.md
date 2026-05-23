---
name: backup-governance
description: Create, verify, restore, and protect encrypted local Git bundle backups without deleting user data.
---

# Backup Governance

Use this before large changes, cleanup, updates, or restore operations.

Rules:

- Never delete backup vault contents.
- Store passwords in Keychain.
- Verify decrypt and clone before calling a backup good.
- Restore into a new folder.
- Never overwrite active workspace without explicit user confirmation.
