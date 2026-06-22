# Missing Parts Specification

## 1. Backup & Restore

### What Gets Backed Up

**Included:**
- SQLite database (chat history)
- Context folder (strategy.md, priorities.md, etc.)
- MemPalace index (semantic search data)
- Settings (LLM provider, integrations)
- Routing table (AGENTS.md)

**Excluded:**
- API keys (stored in Keychain, not backed up)
- Temporary files (logs, cache)
- Large attachments (optional, user-configurable)

### Backup Locations

**Primary:**
- Local: `~/Documents/Executive AI/Backups/`
- Encrypted Git bundle

**Secondary (optional):**
- iCloud: `~/Library/Mobile Documents/com~apple~CloudDocs/Executive AI Backups/`
- NAS: User-specified network path
- External drive: User-specified path

### Backup Schedule

**Options:**
- Automatic: Daily at 3:00 AM (when Mac is awake)
- Manual: User triggers via menu bar or settings
- On-change: After significant changes (new chat, file update)

**Default:** Daily automatic + manual

### Backup Process

```
┌─────────────────────────────────────────┐
│  1. Snapshot SQLite database            │
│     - BEGIN TRANSACTION                 │
│     - Copy to temp location             │
│     - COMMIT                            │
│                                         │
│  2. Copy context folder                 │
│     - Exclude .git, node_modules, etc.  │
│     - Include all .md files             │
│                                         │
│  3. Export MemPalace index              │
│     - Serialize HNSW index              │
│     - Export drawers as JSON            │
│                                         │
│  4. Create encrypted bundle             │
│     - tar.gz all files                  │
│     - Encrypt with AES-256              │
│     - Password from Keychain            │
│                                         │
│  5. Store bundle                        │
│     - Save to backup location           │
│     - Update backup manifest            │
│                                         │
│  6. (Optional) Mirror to secondary      │
│     - Copy to iCloud/NAS                │
│     - Verify integrity                  │
└─────────────────────────────────────────┘
```

### Backup UI

**Menu Bar:**
```
┌────────────────────────────┐
│  📦  Backup Now            │
│  Last backup: 2 hours ago  │
│  Next backup: 3:00 AM      │
└────────────────────────────┘
```

**Settings → Backups:**
```
┌─────────────────────────────────────────┐
│  Backup & Restore                       │
│                                         │
│  Backup Location                        │
│  ┌───────────────────────────────────┐  │
│  │ ~/Documents/Executive AI/Backups/ │  │
│  └───────────────────────────────────┘  │
│  [ Change ]                             │
│                                         │
│  Schedule                               │
│  ○ Manual only                          │
│  ● Daily at 3:00 AM                     │
│  ○ Every 12 hours                       │
│  ○ On significant changes               │
│                                         │
│  Encryption                             │
│  [✓] Encrypt backups (recommended)      │
│  Password: •••••••• [ Change ]          │
│                                         │
│  Backup History                         │
│  ┌───────────────────────────────────┐  │
│  │ 2026-06-22 03:00 · 45MB [Restore] │  │
│  │ 2026-06-21 03:00 · 44MB [Restore] │  │
│  │ 2026-06-20 03:00 · 43MB [Restore] │  │
│  │ [ Show all ]                      │  │
│  └───────────────────────────────────┘  │
│                                         │
│  [ Backup Now ]                         │
│                                         │
└─────────────────────────────────────────┘
```

### Restore Process

**Safe-by-default:** Restore creates a new folder, never overwrites active data.

```
┌─────────────────────────────────────────┐
│  Restore from Backup                    │
│                                         │
│  Select backup to restore:              │
│  ┌───────────────────────────────────┐  │
│  │ ● 2026-06-22 03:00 · 45MB        │  │
│  │ ○ 2026-06-21 03:00 · 44MB        │  │
│  │ ○ 2026-06-20 03:00 · 43MB        │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Restore location:                      │
│  ┌───────────────────────────────────┐  │
│  │ ~/Documents/Executive AI Restore/ │  │
│  └───────────────────────────────────┘  │
│  ⚠️ Will create new folder, won't       │
│     overwrite your current data.        │
│                                         │
│  [ Cancel ]  [ Restore ]                │
│                                         │
└─────────────────────────────────────────┘
```

**After restore:**
1. Backup decrypted to `~/Documents/Executive AI Restore/`
2. User reviews restored data
3. User manually copies needed files to active folder
4. (Optional) User replaces active folder with restored

### Backup Verification

**Integrity check:**
- SHA-256 hash stored in manifest
- Verify before restore
- Alert if corruption detected

**Test restore:**
- Monthly prompt: "Test your backup by restoring to a safe location?"
- User can verify backup works without affecting active data

---

## 2. Error Scenarios

### Network Errors

#### LLM API Unreachable

**Scenario:** User sends message, OpenAI API is down.

**Behavior:**
1. Show error in chat:
```
┌─────────────────────────────────────────┐
│ ⚠️ Connection Error                      │
│                                         │
│ Can't reach OpenAI API.                 │
│ Check your internet connection.         │
│                                         │
│ [ Retry ]  [ Settings ]                 │
└─────────────────────────────────────────┘
```

2. Menu bar icon turns yellow (degraded)
3. User can retry or check settings

**Recovery:**
- Click "Retry" → resend message
- Click "Settings" → check API key, provider

---

#### Telegram Connection Lost

**Scenario:** Nanobot loses connection to Telegram.

**Behavior:**
1. Menu bar icon turns yellow
2. Notification: "Telegram disconnected"
3. Telegram chats show "Offline" badge

**Recovery:**
- Automatic: Nanobot retries every 30 seconds
- Manual: Menu bar → Restart Agent

---

#### WebSocket Disconnected

**Scenario:** Desktop app loses connection to Nanobot.

**Behavior:**
1. Banner at top of app:
```
┌─────────────────────────────────────────┐
│ ⚠️ Connection lost. Reconnecting...     │
└─────────────────────────────────────────┘
```

2. Input disabled
3. Auto-reconnect every 5 seconds

**Recovery:**
- Automatic: Reconnect when Nanobot is back
- Manual: Restart app or Nanobot

---

### LLM Errors

#### Invalid API Key

**Scenario:** User enters wrong API key during onboarding.

**Behavior:**
```
┌─────────────────────────────────────────┐
│  AI Provider                            │
│  ┌───────────────────────────────────┐  │
│  │ OpenAI API Key                    │  │
│  │ ┌───────────────────────────────┐ │  │
│  │ │ sk-invalid...            [👁] │ │  │
│  │ └───────────────────────────────┘ │  │
│  │ ✗ Invalid API key                 │  │
│  │   [ Get a new key from OpenAI ]   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Recovery:**
- User gets new key from OpenAI
- Pastes correct key
- Validation passes

---

#### Rate Limit Exceeded

**Scenario:** User hits OpenAI rate limit.

**Behavior:**
```
┌─────────────────────────────────────────┐
│ ⚠️ Rate Limit Exceeded                   │
│                                         │
│ You've reached the API limit.           │
│ Try again in 1 minute.                  │
│                                         │
│ [ Retry in 60s ]                        │
└─────────────────────────────────────────┘
```

**Recovery:**
- Countdown timer
- Auto-retry when limit resets
- Suggest upgrading plan if frequent

---

#### Model Error (Content Filter)

**Scenario:** LLM refuses to generate response.

**Behavior:**
```
┌─────────────────────────────────────────┐
│ 🤖 Agent                                │
│                                         │
│ I can't help with that request.         │
│ The content may violate usage policies. │
│                                         │
│ [ Regenerate ]  [ Edit message ]        │
└─────────────────────────────────────────┘
```

**Recovery:**
- User edits message
- User tries different phrasing

---

### File System Errors

#### Context Folder Not Found

**Scenario:** User moves or deletes context folder.

**Behavior:**
1. App shows error on launch:
```
┌─────────────────────────────────────────┐
│ ⚠️ Context Folder Missing                │
│                                         │
│ Can't find: ~/Documents/Executive AI/   │
│                                         │
│ [ Select new location ]                 │
│ [ Restore from backup ]                 │
└─────────────────────────────────────────┘
```

**Recovery:**
- User selects new location
- User restores from backup
- User creates new context folder

---

#### Context Folder Not Writable

**Scenario:** Permissions issue, disk full.

**Behavior:**
```
┌─────────────────────────────────────────┐
│ ⚠️ Can't Write to Context Folder         │
│                                         │
│ Check disk space and permissions.       │
│                                         │
│ [ Open in Finder ]  [ Settings ]        │
└─────────────────────────────────────────┘
```

**Recovery:**
- Free disk space
- Fix permissions
- Select different folder

---

#### SQLite Corruption

**Scenario:** Database file corrupted.

**Behavior:**
```
┌─────────────────────────────────────────┐
│ ⚠️ Chat Database Corrupted               │
│                                         │
│ Your chat history is damaged.           │
│ We can try to recover or restore.       │
│                                         │
│ [ Attempt recovery ]                    │
│ [ Restore from backup ]                 │
└─────────────────────────────────────────┘
```

**Recovery:**
- Attempt SQLite `.recover` command
- Restore from backup
- Start fresh (lose chat history)

---

### Integration Errors

#### Telegram Bot Token Invalid

**Scenario:** User revokes bot token in BotFather.

**Behavior:**
1. Menu bar icon turns yellow
2. Settings → Integrations shows error:
```
┌─────────────────────────────────────────┐
│  Telegram                               │
│  ✗ Bot token invalid                    │
│                                         │
│  [ Reconnect ]                          │
└─────────────────────────────────────────┘
```

**Recovery:**
- User generates new token in BotFather
- User pastes new token
- Connection restored

---

#### Transcripted Not Running

**Scenario:** User tries voice input, but Transcripted app is closed.

**Behavior:**
```
┌─────────────────────────────────────────┐
│ ⚠️ Transcripted Not Running              │
│                                         │
│ Open Transcripted app to use voice.     │
│                                         │
│ [ Open Transcripted ]  [ Cancel ]       │
└─────────────────────────────────────────┘
```

**Recovery:**
- Click "Open Transcripted"
- App launches
- Retry voice input

---

### User Errors

#### Accidental Delete

**Scenario:** User deletes important chat.

**Behavior:**
1. Confirmation dialog:
```
┌─────────────────────────────────────────┐
│  Delete Chat?                           │
│                                         │
│  "Strategy Discussion" will be deleted. │
│  This can't be undone.                  │
│                                         │
│  [ Cancel ]  [ Delete ]                 │
└─────────────────────────────────────────┘
```

2. After delete: Toast with undo option:
```
┌─────────────────────────────────────────┐
│  Chat deleted. [ Undo ]                 │
└─────────────────────────────────────────┘
```

**Recovery:**
- Click "Undo" within 10 seconds
- Chat restored

---

#### Accidental Routing

**Scenario:** Agent routes to wrong file.

**Behavior:**
- Routing indicator shows what was updated
- "Undo" button available for 30 seconds

**Recovery:**
- Click "Undo" → changes reverted
- Manual edit if undo not available

---

## 3. File Attachments

### Supported File Types

**Images:**
- PNG, JPG, JPEG, GIF, WebP
- Max size: 10MB
- Preview: Thumbnail in chat

**Documents:**
- PDF, DOCX, XLSX, PPTX
- TXT, MD, CSV, JSON
- Max size: 10MB
- Preview: Icon + filename

**Code:**
- Any text file (.js, .py, .swift, etc.)
- Max size: 5MB
- Preview: Syntax-highlighted snippet

**Archives:**
- ZIP, TAR.GZ
- Max size: 50MB
- Preview: Icon + filename + file count

### Upload Flow

**Drag & Drop:**
1. User drags file onto chat window
2. Drop zone highlights:
```
┌─────────────────────────────────────────┐
│                                         │
│     ┌───────────────────────────────┐   │
│     │                               │   │
│     │     📎 Drop file to attach    │   │
│     │                               │   │
│     └───────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

3. File uploaded
4. Thumbnail/preview appears in input area
5. User can add message text
6. User sends

**Click Attach Button:**
1. User clicks 📎 icon
2. File picker opens
3. User selects file(s)
4. Files uploaded
5. Previews appear in input area
6. User sends

### Storage

**Location:** `context-folder/attachments/[chat-id]/[filename]`

**Example:**
```
~/Documents/Executive AI/
└── attachments/
    ├── tg-denis-123/
    │   ├── 2026-06-22-report.pdf
    │   └── 2026-06-22-screenshot.png
    └── web-456/
        └── 2026-06-22-code.js
```

**Naming:** `[date]-[original-filename]`
- Prevents collisions
- Easy to sort by date

### Agent Access

**How agent reads attachments:**

**Images:**
- Agent can't "see" images directly
- User describes image or asks question
- (Future) Vision API integration

**Documents:**
- PDF: Extract text with `pdftotext`
- DOCX: Extract text with `pandoc`
- TXT/MD: Read directly

**Code:**
- Read directly
- Syntax highlighting in UI

**Example:**
```
User: [attaches report.pdf] What's the main conclusion?

Agent:
1. Extract text from report.pdf
2. Analyze content
3. Response: "The main conclusion is that Q2 revenue increased by 15%..."
```

### UI: Attachment Preview

**In Input Area:**
```
┌─────────────────────────────────────────┐
│ 📎 report.pdf (2.3MB)          [ ✕ ]   │
│ 📎 screenshot.png (1.1MB)      [ ✕ ]   │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ What do you think about this?  [➤] │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**In Message:**
```
┌─────────────────────────────────────────┐
│ 👤 User                                 │
│                                         │
│ What do you think about this?           │
│                                         │
│ 📎 report.pdf (2.3MB)                   │
│    ┌─────────────────────────────────┐  │
│    │ 📄 PDF Document                 │  │
│    │ Q2 Financial Report             │  │
│    │ 12 pages                        │  │
│    └─────────────────────────────────┘  │
│                                         │
│ 📎 screenshot.png (1.1MB)               │
│    ┌─────────────────────────────────┐  │
│    │ [Image thumbnail]               │  │
│    └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Attachment Actions

**Click on attachment:**
- Images: Open in Preview
- Documents: Open in default app
- Code: Open in default editor

**Right-click menu:**
- Open
- Open with...
- Show in Finder
- Download (save copy)
- Delete

### Limits

**Per message:**
- Max files: 5
- Max total size: 50MB

**Per chat:**
- Max attachments: 100
- Max total size: 1GB

**Storage:**
- Attachments count toward context folder size
- User warned when approaching limit

### Cleanup

**Automatic:**
- Attachments from deleted chats removed
- Attachments from archived chats kept (optional)

**Manual:**
- Settings → Storage → "Clean up old attachments"
- User can delete individual attachments

---

## 4. Migration Path

### From CLI (useful-agent) to Desktop App

#### Detection

**On first launch, app checks for existing runtime:**

```
┌─────────────────────────────────────────┐
│  Checking for existing installation...  │
│                                         │
│  ✓ Found useful-agent runtime at:       │
│    ~/Money/Harness/useful-agent-runtime │
│                                         │
│  [ Migrate now ]  [ Start fresh ]       │
│                                         │
└─────────────────────────────────────────┘
```

**Detection locations:**
- `~/Money/Harness/useful-agent-runtime`
- `~/Documents/Useful Agent/`
- Custom location (user specifies)

#### Migration Process

**Step 1: Analyze Existing Runtime**
```
┌─────────────────────────────────────────┐
│  Analyzing existing runtime...          │
│                                         │
│  ✓ Context folder: 45 files             │
│  ✓ MemPalace: 1,234 drawers             │
│  ✓ Telegram bot: @my_executive_bot      │
│  ✓ Chat history: 5,678 messages         │
│  ✓ Backups: 12 bundles                  │
│                                         │
│  [ Continue ]                           │
│                                         │
└─────────────────────────────────────────┘
```

**Step 2: Choose Migration Type**
```
┌─────────────────────────────────────────┐
│  Migration Type                         │
│                                         │
│  ● Full migration (recommended)         │
│    Copy everything to new location      │
│                                         │
│  ○ Link existing runtime                │
│    Use current files, no copy           │
│                                         │
│  ○ Selective migration                  │
│    Choose what to migrate               │
│                                         │
│  [ Continue ]                           │
│                                         │
└─────────────────────────────────────────┘
```

**Step 3: Select Destination**
```
┌─────────────────────────────────────────┐
│  Destination                            │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ ~/Documents/Executive AI/         │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ⚠️ Will copy 234MB of data             │
│                                         │
│  [ Change ]  [ Start migration ]        │
│                                         │
└─────────────────────────────────────────┘
```

**Step 4: Migration Progress**
```
┌─────────────────────────────────────────┐
│  Migrating...                           │
│                                         │
│  ████████████████████░░░░░  80%         │
│                                         │
│  Copying context files...               │
│                                         │
└─────────────────────────────────────────┘
```

**Step 5: Complete**
```
┌─────────────────────────────────────────┐
│  ✓ Migration Complete                   │
│                                         │
│  Your data has been migrated.           │
│                                         │
│  Context: ~/Documents/Executive AI/     │
│  Chats: 5,678 messages imported         │
│  Telegram: Connected                    │
│                                         │
│  [ Start using app ]                    │
│                                         │
└─────────────────────────────────────────┘
```

#### What Gets Migrated

**Context folder:**
- All `.md` files (strategy, priorities, etc.)
- Routing table (AGENTS.md)
- Custom files

**MemPalace:**
- All drawers
- HNSW index (rebuilt if needed)
- Knowledge graph

**Chat history:**
- Nanobot SQLite database → new SQLite schema
- Message mapping (old format → new format)

**Telegram:**
- Bot token (from Nanobot config)
- Allowed user IDs
- Chat history

**Backups:**
- All backup bundles
- Backup manifest

**Settings:**
- LLM provider (if configured)
- API keys (from Keychain)

#### What Doesn't Get Migrated

**Excluded:**
- Temporary files (logs, cache)
- Node modules, Python venvs
- Git history (optional, user choice)

#### Rollback

**If migration fails:**
1. Original runtime untouched
2. Partial migration cleaned up
3. User can retry or start fresh

**If user wants to revert:**
1. Delete new installation
2. Continue using CLI version
3. No data loss

### From Other AI Tools

#### ChatGPT Export

**Scenario:** User has ChatGPT export (JSON/HTML).

**Future feature:** Import ChatGPT conversations into Executive AI.

**Flow:**
1. User exports from ChatGPT
2. Settings → Import → Select export file
3. Conversations imported as chats
4. Messages imported into SQLite

#### Claude Conversations

**Scenario:** User has Claude conversation history.

**Future feature:** Import Claude conversations.

**Challenges:**
- Claude doesn't have export feature
- User would need to copy-paste manually
- (Future) Browser extension to extract

### Migration Testing

**Before migration:**
- Backup existing runtime
- Verify backup integrity

**During migration:**
- Copy to new location
- Verify file counts match
- Verify checksums

**After migration:**
- Test chat history loads
- Test MemPalace search works
- Test Telegram still connected
- Test context files accessible

**User verification:**
- Prompt user to check key data
- "Can you see your recent chats?"
- "Can you search MemPalace?"

---

## Summary

### Backup & Restore
- **What:** SQLite + context + MemPalace + settings
- **Where:** Local + optional iCloud/NAS
- **When:** Daily automatic + manual
- **How:** Encrypted Git bundle
- **Restore:** Safe (new folder, no overwrite)

### Error Scenarios
- **Network:** Retry, check settings, auto-reconnect
- **LLM:** Clear error messages, recovery options
- **File system:** Detect issues, offer solutions
- **Integration:** Status indicators, reconnect options
- **User:** Confirmation dialogs, undo options

### File Attachments
- **Types:** Images, documents, code, archives
- **Upload:** Drag & drop or click attach
- **Storage:** `attachments/[chat-id]/[filename]`
- **Agent access:** Extract text, read code
- **Limits:** 5 files/message, 50MB total

### Migration Path
- **Detection:** Auto-detect existing runtime
- **Options:** Full, link, or selective migration
- **Process:** Analyze → choose → copy → verify
- **Rollback:** Original untouched, can retry
- **Future:** Import from ChatGPT, Claude
