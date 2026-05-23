# Transcripted Module

Transcripted is the meeting/dictation capture layer.

Default source:

- https://transcripted.app/

The installer must guide the user to install from the official site and approve
macOS permissions. The harness then reads:

- `~/Library/Application Support/Transcripted/captures/meetings`
- `~/Library/Application Support/Transcripted/captures/dictations`

The packaged `transcripted-mcp` is a real read-only stdio MCP server backed by
those markdown folders. It implements recent/search/list/read/who_is/recap
tools. It does not install Transcripted itself; if no stable official direct
download is available, install Transcripted manually from the official site and
let `useful-agent doctor` verify the local capture folders.
