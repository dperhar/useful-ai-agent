---
name: memory-reconciliation
description: Keep markdown source files and MemPalace memory aligned after new durable facts or compaction.
---

# Memory Reconciliation

When a durable fact appears:

1. Identify routed markdown target from `AGENTS.md`.
2. Write or propose the markdown update.
3. Add/search MemPalace fact or diary entry.
4. Check for contradictions.
5. Before compaction, summarize what changed and what remains unresolved.
