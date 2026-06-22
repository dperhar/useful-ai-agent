# Executive AI Agent — Detailed Specifications

## 1. Nanobot API Design

### Protocol
- **Transport:** WebSocket (`ws://127.0.0.1:8765`)
- **Format:** JSON-RPC 2.0 over WebSocket
- **Auth:** Local-only (no auth needed, bound to localhost)

### Connection Lifecycle

```
Desktop App                          Nanobot
    │                                   │
    │──── WS Connect ──────────────────→│
    │                                   │
    │←─── Connection Ack ──────────────│
    │     { version, capabilities }     │
    │                                   │
    │──── Subscribe to events ─────────→│
    │     { method: "subscribe",        │
    │       params: ["chats", "msgs"] } │
    │                                   │
    │←─── Subscription confirmed ──────│
    │                                   │
    │     [Real-time events flow]       │
    │                                   │
```

### API Methods

#### Chat Management

**`chat.list`** — Get all chats
```json
// Request
{
  "jsonrpc": "2.0",
  "method": "chat.list",
  "params": {
    "source": "all",        // "telegram" | "web" | "cli" | "all"
    "archived": false,
    "limit": 50,
    "offset": 0
  },
  "id": 1
}

// Response
{
  "jsonrpc": "2.0",
  "result": {
    "chats": [
      {
        "id": "tg-denis-123",
        "source": "telegram",
        "title": "Denis",
        "last_message": "What's my schedule?",
        "updated_at": 1719000000,
        "unread": 2,
        "pinned": true
      }
    ],
    "total": 15
  },
  "id": 1
}
```

**`chat.create`** — Create new chat session
```json
{
  "method": "chat.create",
  "params": {
    "source": "web",
    "title": "New conversation"
  }
}
```

**`chat.get`** — Get chat with messages
```json
{
  "method": "chat.get",
  "params": {
    "id": "tg-denis-123",
    "messages_limit": 50,
    "messages_before": null  // timestamp for pagination
  }
}
```

**`chat.delete`** — Delete chat
```json
{
  "method": "chat.delete",
  "params": { "id": "tg-denis-123" }
}
```

**`chat.pin`** / **`chat.unpin`** / **`chat.archive`**

#### Messaging

**`message.send`** — Send message
```json
{
  "method": "message.send",
  "params": {
    "chat_id": "tg-denis-123",
    "content": "What's my schedule today?",
    "attachments": []  // file paths
  }
}

// Response (immediate ack)
{
  "result": {
    "message_id": "msg-456",
    "status": "sent"
  }
}

// Later: streaming response via events
```

**`message.edit`** — Edit user message (re-run with new input)
```json
{
  "method": "message.edit",
  "params": {
    "message_id": "msg-456",
    "new_content": "What's my schedule this week?"
  }
}
```

**`message.regenerate`** — Regenerate assistant response
```json
{
  "method": "message.regenerate",
  "params": {
    "message_id": "msg-789"  // assistant message to regenerate
  }
}
```

**`message.delete`** — Delete message

#### Settings

**`settings.get`** — Get current settings
```json
{
  "method": "settings.get",
  "params": {}
}

// Response
{
  "result": {
    "llm": {
      "provider": "openai",
      "model": "gpt-4o",
      "temperature": 0.7
    },
    "context": {
      "folder": "/Users/denis/Documents/Executive AI",
      "mem_palace_enabled": true
    },
    "integrations": {
      "telegram": { "connected": true, "bot_username": "@my_bot" },
      "transcripted": { "connected": false }
    }
  }
}
```

**`settings.update`** — Update settings
```json
{
  "method": "settings.update",
  "params": {
    "llm.model": "claude-3-5-sonnet",
    "llm.temperature": 0.5
  }
}
```

**`settings.test_llm`** — Test LLM connection
```json
{
  "method": "settings.test_llm",
  "params": {
    "provider": "openai",
    "api_key": "sk-..."
  }
}
```

#### System

**`system.status`** — Get agent status
```json
{
  "method": "system.status",
  "params": {}
}

// Response
{
  "result": {
    "status": "running",  // "running" | "degraded" | "stopped"
    "uptime": 3600,
    "services": {
      "nanobot": "ok",
      "telegram": "ok",
      "mem_palace": "ok",
      "transcripted": "disconnected"
    },
    "context_tokens": 12400,
    "last_backup": 1718996400
  }
}
```

**`system.restart`** — Restart agent
**`system.backup`** — Trigger backup
**`system.logs`** — Get recent logs

### Real-time Events (Server → Client)

**`event.message`** — New message
```json
{
  "method": "event.message",
  "params": {
    "type": "new_message",
    "chat_id": "tg-denis-123",
    "message": {
      "id": "msg-456",
      "role": "assistant",
      "content": "Here's your schedule...",
      "created_at": 1719000000,
      "streaming": false
    }
  }
}
```

**`event.message_stream`** — Streaming response chunk
```json
{
  "method": "event.message_stream",
  "params": {
    "message_id": "msg-456",
    "chunk": "Here's your",
    "done": false
  }
}
```

**`event.chat_updated`** — Chat metadata changed
**`event.status`** — Agent status changed
**`event.backup`** — Backup completed

### Error Handling

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid request",
    "data": { "details": "Missing required field: chat_id" }
  },
  "id": 1
}
```

**Error codes:**
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32000`: LLM provider error
- `-32001`: Context folder not found
- `-32002`: Integration not connected

---

## 2. Chat Session Model

### What is a "Chat"?

A **chat** is a conversation thread with:
- Unique ID
- Source (telegram/web/cli)
- Title (auto or manual)
- Messages (ordered by time)
- Metadata (pinned, archived, tags)

### Session Types

#### Type 1: Persistent Chats (Telegram)
- **Created:** When user first messages via Telegram
- **Lifetime:** Infinite (until manually deleted)
- **Context:** Accumulates over time
- **Use case:** Daily conversations with agent

#### Type 2: Ephemeral Sessions (Web/CLI)
- **Created:** User clicks "New Chat"
- **Lifetime:** Until archived or deleted
- **Context:** Isolated per session
- **Use case:** Focused tasks, experiments

#### Type 3: Context-Linked Sessions
- **Created:** User starts chat with specific context (e.g., "Discuss Q2 report")
- **Lifetime:** Until task complete
- **Context:** Pre-loaded with relevant files
- **Use case:** Project-specific discussions

### Context Isolation

**Question:** Should each chat have isolated context, or share global context?

**Answer:** Hybrid approach

```
┌─────────────────────────────────────────┐
│           Global Context                │
│  (strategy.md, priorities.md, etc.)     │
│  ─── Always available to agent ───      │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Chat A  │ │ Chat B  │ │ Chat C  │
   │(Telegram│ │  (Web)  │ │  (CLI)  │
   │         │ │         │ │         │
   │ Local:  │ │ Local:  │ │ Local:  │
   │ - msgs  │ │ - msgs  │ │ - msgs  │
   │ - notes │ │ - code  │ │ - logs  │
   └─────────┘ └─────────┘ └─────────┘
```

**Global context:** Source-of-truth files (strategy, priorities, etc.)
**Local context:** Chat-specific messages and attachments

**Agent sees:** Global + current chat's local context

### Multi-Chat Behavior

**Scenario:** User has Telegram chat open, starts new Web chat

- **Telegram chat:** Continues in background, messages queue
- **Web chat:** Fresh session, isolated context
- **Switching:** Click chat in sidebar → loads that chat's messages
- **Notifications:** Desktop notification for new Telegram messages

### Chat Lifecycle

```
Created → Active → (Idle) → Archived → Deleted
   │         │        │         │
   │         │        │         └── Read-only, excluded from search
   │         │        └── No activity for 30 days
   │         └── User is actively chatting
   └── New chat started
```

### Chat Metadata

```typescript
interface Chat {
  id: string;                    // "tg-denis-123" or "web-456"
  source: 'telegram' | 'web' | 'cli' | 'api';
  title: string;                 // Auto-generated or manual
  created_at: number;            // Unix timestamp
  updated_at: number;            // Last message time
  
  // UI state
  pinned: boolean;
  archived: boolean;
  unread: number;                // Unread message count
  tags: string[];                // User-defined labels
  
  // Context
  context_files?: string[];      // Linked files (for context-linked sessions)
  summary?: string;              // Auto-generated summary
  
  // Telegram-specific
  telegram_user_id?: string;
  telegram_username?: string;
}
```

---

## 3. Chat Features Detail

### MVP Features (v1.0)

#### Core Messaging
- ✅ Send text messages
- ✅ Receive streaming responses
- ✅ Markdown rendering (bold, italic, lists, links)
- ✅ Code blocks with syntax highlighting
- ✅ Copy message content
- ✅ Copy code block

#### Chat Management
- ✅ Chat list (sidebar)
- ✅ Create new chat
- ✅ Switch between chats
- ✅ Unread indicators
- ✅ Pin chats
- ✅ Delete chats

#### Context
- ✅ Show "context used" indicator
- ✅ Link to source files

#### Input
- ✅ Auto-growing textarea
- ✅ Send with ⌘+Enter
- ✅ Character/token counter

### Should Have (v1.1)

#### Messaging
- 🔄 Edit user message (re-run)
- 🔄 Regenerate response
- 🔄 Message reactions (👍👎)
- 🔄 Share message (copy link)

#### Chat Management
- 🔄 Archive chats
- 🔄 Search across all chats
- 🔄 Tags/labels
- 🔄 Chat summary (auto-generated)

#### Input
- 🔄 File attachments (drag & drop)
- 🔄 Voice input (Transcripted integration)
- 🔄 Slash commands (/backup, /settings)

#### Context
- 🔄 Expandable "context used" panel
- 🔄 "Add to context" button (pin file to chat)
- 🔄 Memory indicators (what MemPalace contributed)

### Nice to Have (v2.0)

#### Messaging
- 🌟 Message threads (reply to specific message)
- 🌟 Forward message to another chat
- 🌟 Export chat (markdown/PDF)
- 🌟 Image generation (via $imagegen)

#### Chat Management
- 🌟 Chat folders (group chats)
- 🌟 Smart suggestions ("Archive old chats?")
- 🌟 Chat templates (pre-configured contexts)

#### Input
- 🌟 Autocomplete (from context)
- 🌟 Prompt library (saved prompts)
- 🌟 Multi-line with formatting toolbar

#### Collaboration (future)
- 🌟 Share chat with team
- 🌟 Comment on messages
- 🌟 Assign tasks from chat

### Feature Specifications

#### Markdown Rendering

**Supported:**
- `**bold**`, `*italic*`, `~~strikethrough~~`
- `[link](url)`
- `- list`, `1. numbered list`
- `` `inline code` ``
- ```` ```code block``` ````
- `> blockquote`
- `# heading` (h1-h6)
- `---` horizontal rule
- Tables (basic)

**Not supported:**
- HTML tags (sanitized)
- JavaScript (blocked)
- External images (unless whitelisted)

#### Code Blocks

```javascript
// Syntax highlighting for 50+ languages
function hello() {
  console.log("Hello, world!");
}
```

**Features:**
- Language detection (auto or manual)
- Copy button (top-right)
- Line numbers (optional)
- "Explain code" button (future)

#### Streaming Responses

**Behavior:**
1. User sends message
2. "Agent is typing..." indicator
3. Response streams in real-time
4. Cursor blinks at end during streaming
5. "Stop generating" button available
6. Final message renders with full markdown

**Edge cases:**
- Network error → "Connection lost. Retry?" button
- LLM error → Error message with "Regenerate" option
- User sends new message during streaming → Queue or interrupt?

#### File Attachments

**Supported types:**
- Images: PNG, JPG, GIF, WebP
- Documents: PDF, DOCX, TXT, MD
- Code: Any text file

**Behavior:**
1. Drag & drop or click attach button
2. File uploaded to context folder
3. Thumbnail/preview in chat
4. Agent can read file content
5. File path stored in message metadata

**Limits:**
- Max file size: 10MB
- Max files per message: 5

#### Voice Input (Transcripted)

**Flow:**
1. User clicks 🎙 button
2. Recording starts (visual indicator)
3. User speaks
4. Click 🎙 again or auto-stop on silence
5. Audio sent to Transcripted
6. Transcript appears in input field
7. User can edit before sending

**Requirements:**
- Transcripted app installed and running
- MCP connection established

---

## 4. MVP Scope (v1.0)

### Must Have (Launch Blockers)

#### Installation
- [ ] DMG with notarized app
- [ ] Drag-to-Applications install
- [ ] First launch: Gatekeeper handling
- [ ] System requirements check (macOS 13+, Apple Silicon)

#### Onboarding
- [ ] Welcome screen
- [ ] LLM provider setup (OpenAI API key)
- [ ] Context folder selection (default or custom)
- [ ] Basic feature tour (3 screens)

#### Main Interface
- [ ] Chat list (sidebar)
- [ ] Chat view (messages)
- [ ] Send/receive messages
- [ ] Markdown rendering
- [ ] Code blocks with copy
- [ ] Streaming responses

#### Telegram Integration
- [ ] Connect existing Telegram bot
- [ ] Display Telegram chats in unified inbox
- [ ] Send/receive via Telegram
- [ ] Real-time message sync

#### Settings (WebView)
- [ ] Settings window (embedded)
- [ ] LLM provider settings
- [ ] Context folder settings
- [ ] Telegram connection status

#### Menu Bar
- [ ] Menu bar icon with status
- [ ] Open main window
- [ ] Quick actions (restart, backup)
- [ ] Quit

#### Background
- [ ] Nanobot integration
- [ ] WebSocket connection
- [ ] SQLite for chat storage
- [ ] Auto-start on login (optional)

### Should Have (v1.1, within 2 weeks)

- [ ] Edit user message
- [ ] Regenerate response
- [ ] Search across chats
- [ ] Pin/archive chats
- [ ] File attachments
- [ ] Voice input (Transcripted)
- [ ] Chat export (markdown)
- [ ] Notifications (desktop alerts)

### Nice to Have (v2.0, within 2 months)

- [ ] Multi-provider support (Claude, Ollama)
- [ ] Chat tags/labels
- [ ] Chat templates
- [ ] Image generation
- [ ] Browser extension
- [ ] Calendar integration
- [ ] Email integration

### Out of Scope (Not Planned)

- ❌ Windows/Linux support
- ❌ Mobile app
- ❌ Cloud sync (iCloud sync maybe later)
- ❌ Team collaboration
- ❌ Self-hosted LLM training
- ❌ Plugin system (for now)

### Success Metrics (v1.0)

**Technical:**
- App launches in <2 seconds
- Message send-to-display latency <500ms
- Zero crashes in first 24 hours
- Telegram sync delay <3 seconds

**User:**
- User completes onboarding in <5 minutes
- User sends first message within 1 minute of launch
- User connects Telegram within first session
- User returns next day (D1 retention)

---

## 5. Onboarding UX (Simplified)

### Current Flow (4 steps)
1. Welcome
2. LLM Provider
3. Context Storage
4. Integrations + Tour

### Simplified Flow (3 steps)

#### Step 1: Welcome + Quick Setup
```
┌─────────────────────────────────────────┐
│                                         │
│     Executive AI Agent                  │
│     Your personal AI chief of staff     │
│                                         │
│     ┌───────────────────────────────┐   │
│     │  Get Started                  │   │
│     └───────────────────────────────┘   │
│                                         │
│     Already using useful-agent?         │
│     [ Connect existing runtime ]        │
│                                         │
└─────────────────────────────────────────┘
```

#### Step 2: One-Page Setup
```
┌─────────────────────────────────────────┐
│  Let's set up your agent                │
│                                         │
│  AI Provider                            │
│  ┌───────────────────────────────────┐  │
│  │ OpenAI API Key                    │  │
│  │ ┌───────────────────────────────┐ │  │
│  │ │ sk-...                   [👁] │ │  │
│  │ └───────────────────────────────┘ │  │
│  │ ✓ Validated · gpt-4o              │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Storage Location                       │
│  ┌───────────────────────────────────┐  │
│  │ ~/Documents/Executive AI/    [📁] │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Telegram (optional)                    │
│  ┌───────────────────────────────────┐  │
│  │ [ Connect Telegram ]              │  │
│  └───────────────────────────────────┘  │
│                                         │
│              [ Skip ]  [ Continue ]     │
│                                         │
└─────────────────────────────────────────┘
```

**Key changes:**
- All settings on one page
- Telegram is optional (can connect later)
- Validation happens inline
- "Skip" option for everything

#### Step 3: Ready!
```
┌─────────────────────────────────────────┐
│                                         │
│              ✓ You're all set!          │
│                                         │
│     Your agent is ready to help.        │
│                                         │
│     ┌───────────────────────────────┐   │
│     │  Start Chatting               │   │
│     └───────────────────────────────┘   │
│                                         │
│     ─── or ───                          │
│                                         │
│     [ Watch 2-min tour ]                │
│     [ Read docs ]                       │
│                                         │
└─────────────────────────────────────────┘
```

**Key changes:**
- Tour is optional (video or docs)
- Primary CTA is "Start Chatting"
- User can skip directly to app

### Magic Link Alternative (Future)

**Idea:** Instead of manual API key entry, use "magic link" flow:

1. User clicks "Sign in with OpenAI"
2. Opens browser to `auth.opencode.ai/connect`
3. User logs in with OpenAI
4. Redirects back to app with token
5. Token stored in Keychain

**Benefits:**
- No copy-paste API keys
- Automatic validation
- Can manage subscription in browser

**Challenges:**
- Requires Opencode Go OAuth integration
- OpenAI doesn't support OAuth for API keys
- Need custom auth server

**Recommendation:** Implement for Opencode Go in v1.1, keep manual API key for OpenAI/Anthropic in v1.0

### Onboarding States

#### Happy Path
1. Welcome → Get Started
2. Paste API key → Validated ✓
3. Default storage → Continue
4. Skip Telegram → Continue
5. Ready → Start Chatting
6. **Time: 2 minutes**

#### Connect Existing Runtime
1. Welcome → Connect existing
2. Select runtime folder → Detected ✓
3. Auto-import settings → Continue
4. Ready → Start Chatting
5. **Time: 30 seconds**

#### Errors & Recovery

**Invalid API key:**
```
│  AI Provider                            │
│  ┌───────────────────────────────────┐  │
│  │ OpenAI API Key                    │  │
│  │ ┌───────────────────────────────┐ │  │
│  │ │ sk-invalid...            [👁] │ │  │
│  │ └───────────────────────────────┘ │  │
│  │ ✗ Invalid key. Check and retry.   │  │
│  │   [ Get a new key from OpenAI ]   │  │
│  └───────────────────────────────────┘  │
```

**Storage folder not writable:**
```
│  Storage Location                       │
│  ┌───────────────────────────────────┐  │
│  │ /System/Protected/           [📁] │  │
│  └───────────────────────────────────┘  │
│  ✗ Can't write to this folder.         │
│    Choose a different location.         │
```

**Telegram connection failed:**
```
│  Telegram (optional)                    │
│  ┌───────────────────────────────────┐  │
│  │ ✗ Connection failed          [↻] │  │
│  └───────────────────────────────────┘  │
│  You can connect Telegram later in      │
│  Settings.                              │
```

### Progressive Disclosure

**Show immediately:**
- LLM provider (required)
- Storage location (required)

**Show on first use:**
- Telegram integration (when user opens chat)
- Voice input (when user clicks 🎙)
- File attachments (when user drags file)

**Show in settings:**
- Advanced options (temperature, max tokens)
- Backup configuration
- Transcripted integration

---

## Summary

### Architecture Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | Swift + WKWebView | Native feel, small bundle |
| Chat storage | SQLite | Fast, indexed, embedded |
| Semantic layer | MemPalace | Agent retrieval |
| LLM gateway | Nanobot | Unified API, context management |
| Telegram | Nanobot WebSocket | Real-time, existing integration |
| Settings | WebView | Flexible UI, easy to iterate |

### MVP Scope

**v1.0 (Launch):**
- DMG install
- 3-step onboarding
- Unified chat inbox
- Telegram integration
- Basic chat features
- Menu bar app

**v1.1 (2 weeks):**
- Edit/regenerate messages
- Search
- File attachments
- Voice input

**v2.0 (2 months):**
- Multi-provider
- Advanced features
- Integrations

### Next Steps

1. **Validate specs** — Review this document
2. **Design in Figma** — Create mockups from spec
3. **Scaffold project** — Xcode + React setup
4. **Build MVP** — Core features first
5. **Test with users** — Iterate on feedback
