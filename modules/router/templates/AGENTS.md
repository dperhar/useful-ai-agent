# Useful AI Agent Router

This is the canonical runtime entrypoint for this workspace.
Keep it short. Detailed context lives in scoped files and local memory.

## Load Order

For every task:

1. Read this file first.
2. Identify the target path.
3. Read every `AGENTS.md` from this workspace root down to that target path.
4. Read root-to-leaf. Deeper files override broader files.
5. Do not read sibling scoped routers unless the task explicitly touches them.

Examples:

- `Projects/Acme/Plan.md` -> read root, then `Projects/AGENTS.md` if present, then `Projects/Acme/AGENTS.md` if present.
- `Harness/bin/backup.sh` -> read root, then `Harness/AGENTS.md`.
- `Clients/Acme/Call notes.md` -> read root, then `Clients/AGENTS.md` if present, then client router if present.

## Sacred Rules

- Never permanently delete user files. Move to `Archive/` or ask.
- Do not create random new `.md` files. Use the routing table or ask.
- Context `.md` files are source of truth; local memory is retrieval/write support.
- Never print secrets, tokens, passwords, OAuth data, Telegram bot tokens, or backup passphrases.
- Never delete, unlock, overwrite, or weaken external backup vaults.

## Routing Table

- Stable identity, principles, operating model: `Canon/`
- Current work and active projects: `Projects/`
- Client-specific notes, calls, audits, proposals: `Clients/`
- Personal life/admin context: `Personal/`
- Unsorted raw input that needs routing: `Inbox/`
- Runtime scripts, agent ops, backups, local setup: `Harness/`
- Old or completed material: `Archive/`

## Memory Protocol

- Before answering from past context, read routed source files or query local memory.
- Store durable new facts in local memory and propose a routed `.md` reconciliation.
- Use Transcripted meeting context read-only and cite date/title/filename when relevant.
- Before compaction, summarize durable facts and update routed files or memory.

## Tool Notes

- Use `/improve` for high-stakes quality, MECE review, and source reconciliation.
- Use context setup/cleanup skills for architecture maintenance.
- Use backup governance before destructive or large-file operations.
