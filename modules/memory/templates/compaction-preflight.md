# Compaction Preflight

Before compacting or ending a long agent session:

1. List durable facts learned in this session.
2. Search local memory for contradictions.
3. Propose routed `.md` updates.
4. Add accepted facts to MemPalace.
5. Record unresolved decisions.
6. Run `useful-agent check` if runtime/config changed.
