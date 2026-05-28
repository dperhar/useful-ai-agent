# Agent-Led macOS Install

This is the installation script for the human's AI agent.

## Phase 1: Inspect

1. Read `README.md`.
2. Read `docs/security-privacy.md`.
3. Read `docs/source-allowlist.md`.
4. Confirm the Mac is Apple Silicon.

## Phase 2: Bootstrap

Ask the user which project folder should become the agent workspace. The runtime
must be installed inside that project folder, not in a disconnected home-folder
workspace. Then run the README bootstrap after showing it to the user:

```zsh
curl -fsSL https://raw.githubusercontent.com/dperhar/useful-ai-agent/main/bootstrap/macos.sh -o /tmp/useful-agent-bootstrap.sh
less /tmp/useful-agent-bootstrap.sh
zsh /tmp/useful-agent-bootstrap.sh
```

## Phase 3: Manual Guidance

Guide the user through:

- Choosing the project root and confirming the runtime folder.
- BotFather bot creation and token paste.
- Transcripted official install and permissions.
- AI app login.
- macOS file access prompts.

## Phase 4: Verify

Run:

```zsh
useful-agent check
```

Fix every actionable warning. Do not invent success.
