# Memory Module

## Source Of Truth

Markdown files in the workspace are canonical. Use MemPalace for retrieval,
diary, graph facts, and cross-project context.

## Default Taxonomy

- `user`
- `projects`
- `clients`
- `meetings`
- `agent_ops`
- `archive`

## Reconciliation

When a durable fact is learned:

1. Store it in MemPalace.
2. Propose a routed `.md` update.
3. Do not create new files unless the router says where they belong.
4. Before compaction, summarize facts and unresolved decisions.
