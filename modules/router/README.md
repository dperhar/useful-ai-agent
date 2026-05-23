# Router Module

Installs native instruction files for agents:

- `AGENTS.md`
- scoped `AGENTS.md`
- `CLAUDE.md`
- `.cursor/rules/*.mdc`

Core rule: read root router, then every scoped router on the path to the target
file, root-to-leaf. Never load sibling routers unless the task touches them.
