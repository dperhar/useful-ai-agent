# Chat Storage Research

## Question
Где хранить историю чатов в Executive AI Agent?

## Options Analysis

### Option 1: SQLite

**Pros:**
- ✅ Embedded — no server needed, single file
- ✅ Fast queries — indexed search across millions of messages
- ✅ FTS5 — full-text search built-in
- ✅ Transactions — ACID compliance, no corruption
- ✅ Compact — efficient storage (~100K messages ≈ 50MB)
- ✅ Pagination — trivial to implement "load older messages"
- ✅ Metadata — easy to store timestamps, source, attachments, etc.
- ✅ Backup — single file, easy to encrypt and backup

**Cons:**
- ❌ Not human-readable — can't open in text editor
- ❌ Agent can't read directly — needs MCP tools or API
- ❌ Schema migrations — need versioning strategy
- ❌ Binary format — harder to debug

**Best for:** Primary storage, fast UI, large history

---

### Option 2: Markdown Files

**Pros:**
- ✅ Human-readable — open in any editor
- ✅ Agent reads directly — no tools needed
- ✅ Git-friendly — version control, diff, merge
- ✅ Existing pattern — matches useful-agent architecture
- ✅ Easy backup — just copy files
- ✅ Portable — user can migrate manually

**Cons:**
- ❌ Slow search — grep across thousands of files
- ❌ No transactions — concurrent writes can corrupt
- ❌ No indexing — "find message from 3 months ago" is slow
- ❌ Pagination hard — need to parse files to count messages
- ❌ Metadata awkward — where to store timestamps, source, etc.?
- ❌ File sprawl — one file per chat? per day? per month?

**Best for:** Export, archival, agent context (not primary storage)

---

### Option 3: MemPalace

**Pros:**
- ✅ Semantic search — find by meaning, not keywords
- ✅ Already integrated — agent knows how to use it
- ✅ Knowledge graph — relationships between entities
- ✅ Cross-session memory — persists across chats

**Cons:**
- ❌ Not designed for sequential chat — no "scroll up" concept
- ❌ Slow for large volumes — HNSW index can bottleneck
- ❌ No pagination — can't "load 50 older messages"
- ❌ Embedding cost — every message = API call
- ❌ Overkill for raw history — semantic search not needed for every message
- ❌ Conflict potential — MemPalace for retrieval, not storage

**Best for:** Semantic retrieval layer (not primary storage)

---

### Option 4: PostgreSQL/MongoDB

**Pros:**
- ✅ Powerful queries — aggregations, joins, etc.
- ✅ Scalable — can handle any volume
- ✅ Mature ecosystem — ORMs, tools, monitoring

**Cons:**
- ❌ Server required — user needs to install and run
- ❌ Overkill for desktop app — adds complexity
- ❌ Not embedded — network, auth, configuration
- ❌ Backup complexity — pg_dump, mongodump, etc.

**Best for:** Server-side apps, not desktop

---

## Recommended Architecture: Hybrid

### Primary Storage: SQLite
- **What:** All messages stored in SQLite database
- **Why:** Fast, compact, reliable, embedded
- **Schema:**
  ```sql
  CREATE TABLE chats (
    id TEXT PRIMARY KEY,
    source TEXT, -- 'telegram', 'web', 'cli'
    title TEXT,
    created_at INTEGER,
    updated_at INTEGER,
    pinned BOOLEAN DEFAULT 0,
    archived BOOLEAN DEFAULT 0
  );

  CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    chat_id TEXT REFERENCES chats(id),
    role TEXT, -- 'user', 'assistant', 'system'
    content TEXT,
    created_at INTEGER,
    metadata TEXT -- JSON: attachments, context used, etc.
  );

  CREATE VIRTUAL TABLE messages_fts USING fts5(content, content='messages');
  ```

### Semantic Layer: MemPalace
- **What:** Important messages/conclusions indexed in MemPalace
- **Why:** Agent can search by meaning across all chats
- **When to index:**
  - User explicitly says "remember this"
  - Agent detects important decision/fact
  - End of long conversation (auto-summarize)
- **Not indexed:** Every "hi", "thanks", small talk

### Export/Backup: Markdown
- **What:** Periodic export to markdown files
- **Why:** Human-readable backup, git-friendly, agent context
- **Format:** One file per chat or per month
- **Location:** `context-folder/chats/` (archived layer)

---

## Data Flow

```
User types message
       ↓
Desktop App (Swift + WebView)
       ↓
Send to Nanobot (WebSocket)
       ↓
Nanobot:
  1. Store message in SQLite
  2. Build context (MemPalace search + files)
  3. Call LLM with context
  4. Store response in SQLite
  5. (Optional) Index important facts in MemPalace
       ↓
Return response to Desktop App
       ↓
Desktop App:
  1. Display message
  2. Update UI from SQLite (real-time)
```

---

## Agent Access Patterns

### Pattern 1: "What did we discuss yesterday?"
- **Storage:** SQLite
- **Query:** `SELECT * FROM messages WHERE created_at > yesterday ORDER BY created_at`
- **Fast:** Yes (indexed)

### Pattern 2: "What did I say about the investor meeting?"
- **Storage:** MemPalace (semantic) + SQLite (full-text)
- **Query:** MemPalace search "investor meeting" → get message IDs → fetch from SQLite
- **Fast:** Yes (semantic + indexed)

### Pattern 3: "Summarize our last 10 conversations"
- **Storage:** SQLite
- **Query:** `SELECT * FROM messages WHERE chat_id IN (last 10 chats)`
- **Fast:** Yes (indexed, paginated)

### Pattern 4: "What decisions did I make this month?"
- **Storage:** MemPalace (KG)
- **Query:** KG query for decisions with time filter
- **Fast:** Yes (if indexed)

---

## Conflict Resolution

### Problem: MemPalace vs SQLite
- **MemPalace:** "I remember X" (semantic)
- **SQLite:** "Here's exactly what was said" (verbatim)

### Solution: Clear separation
- **SQLite:** Source of truth for "what was said"
- **MemPalace:** Index for "what matters" (decisions, facts, preferences)
- **Agent rule:** When asked about past conversations, search MemPalace first for relevance, then fetch exact messages from SQLite

### Problem: Agent reads files vs database
- **Files:** `strategy.md`, `priorities.md` (source of truth)
- **Database:** Chat history (not source of truth for decisions)

### Solution: Routing
- **Decisions/facts:** Written to both chat (SQLite) AND source-of-truth files (markdown)
- **Chat history:** Only in SQLite (not duplicated to files unless exported)
- **Agent reads:** Files for context, MemPalace for retrieval, SQLite for chat history

---

## Migration from CLI

### Existing useful-agent users:
- **Current state:** Telegram chats in Nanobot (likely SQLite or files)
- **Migration:** 
  1. Detect existing Nanobot runtime
  2. Import chat history to new SQLite schema
  3. Preserve MemPalace index (no re-embedding needed)

### New users:
- **Start fresh:** Empty SQLite database
- **Onboarding:** Connect Telegram → new chats start flowing in

---

## Implementation Notes

### SQLite Library
- **Swift:** `sqlite3` (built-in) or `GRDB.swift` (ORM)
- **Recommendation:** GRDB — type-safe, migrations, FTS5 support

### MemPalace Integration
- **When to index:**
  - User says "remember this" / "запомни"
  - Agent detects: decision, fact, preference, deadline
  - Conversation ends with summary
- **What to index:**
  - Key decisions ("We decided to use Tauri")
  - Facts ("Investor meeting is on Friday")
  - Preferences ("I prefer dark mode")
  - Not: greetings, acknowledgments, small talk

### Backup Strategy
- **SQLite:** Include in encrypted backup bundle
- **MemPalace:** Already backed up (part of runtime)
- **Markdown exports:** Optional, for human-readable archive

---

## Open Questions

1. **Message editing:** If user edits message in Telegram, update in SQLite?
2. **Deletion:** "Forget this conversation" — delete from SQLite + MemPalace?
3. **Sync:** Multiple devices? (future: iCloud sync of SQLite)
4. **Retention:** Auto-archive chats older than X months?
5. **Export format:** Markdown? JSON? Both?

---

## Recommendation

**Use SQLite as primary storage + MemPalace for semantic retrieval + Markdown for export.**

This gives:
- Fast UI (SQLite)
- Smart agent (MemPalace)
- Human-readable backup (Markdown)
- No conflicts (clear separation of concerns)
