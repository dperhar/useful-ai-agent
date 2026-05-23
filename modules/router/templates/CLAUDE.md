# Claude Wrapper

Claude Code must treat `AGENTS.md` as the canonical runtime router.

For any task in this workspace:

1. Read `AGENTS.md`.
2. Follow its scoped-router load order exactly.
3. Read only scoped `AGENTS.md` files on the path to the task target.

Do not duplicate the router here. Add only Claude-specific notes if needed.
