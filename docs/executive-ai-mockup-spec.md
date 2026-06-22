# Executive AI Agent — Mockup Specification

> For Figma design. Tech: Swift + WKWebView (native macOS shell, web UI inside).

---

## Design System

### Colors
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--bg-primary` | `#FFFFFF` | `#1A1A2E` | Main background |
| `--bg-secondary` | `#F5F5F7` | `#16213E` | Sidebar, cards |
| `--bg-tertiary` | `#E8E8ED` | `#0F3460` | Hover states |
| `--text-primary` | `#1D1D1F` | `#F5F5F7` | Main text |
| `--text-secondary` | `#86868B` | `#A0A0A8` | Muted text |
| `--accent` | `#007AFF` | `#0A84FF` | Buttons, links |
| `--success` | `#34C759` | `#30D158` | Online, confirmed |
| `--warning` | `#FF9500` | `#FF9F0A` | Alerts |
| `--error` | `#FF3B30` | `#FF453A` | Errors, delete |

### Typography
| Role | Font | Size | Weight |
|------|------|------|--------|
| Display | SF Pro Display | 28px | Bold |
| Title | SF Pro Text | 20px | Semibold |
| Body | SF Pro Text | 15px | Regular |
| Caption | SF Pro Text | 12px | Regular |
| Code | SF Mono | 13px | Regular |

### Spacing
- Base unit: 8px
- Common: 8, 16, 24, 32, 48px

### Border Radius
- Small: 6px (buttons, inputs)
- Medium: 12px (cards)
- Large: 16px (modals)

---

## Screen 1: Welcome

**Window:** 600×500px, centered, no resize

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│                                                      │
│                    [App Icon 80px]                   │
│                                                      │
│              Executive AI Agent                      │
│         Your personal AI chief of staff              │
│                                                      │
│                                                      │
│              ┌─────────────────────┐                 │
│              │    Get Started      │                 │
│              └─────────────────────┘                 │
│                                                      │
│              Version 1.0 · © 2026                    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**States:**
- Default
- Loading (spinner on button during init)

---

## Screen 2: Onboarding — LLM Provider

**Window:** 640×560px

```
┌──────────────────────────────────────────────────────┐
│  ● ● ●                                    1 of 4     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Connect Your AI Provider                            │
│  Choose how your agent will think                    │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  ◉  OpenAI API                    Recommended  │  │
│  │     GPT-4, GPT-4o, o1-pro                      │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  ○  Opencode Go                               │  │
│  │     Subscription-based, multi-model            │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  ○  Anthropic (Claude)                         │  │
│  │     Claude 3.5 Sonnet, Opus                    │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  ○  Local Model (Ollama)                       │  │
│  │     Run models on your Mac, fully offline      │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  ○  Skip — configure later                    │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│                              [ Back ]  [ Continue ]  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**States:**
- Default (no selection)
- Provider selected (blue border on card)
- API key input expanded (after selecting OpenAI/Anthropic)
- OAuth flow (after selecting Opencode Go)
- Validation error (red border, error message)
- Loading (validating key)

### Sub-screen: API Key Input

Appears inline when OpenAI or Anthropic selected:

```
│  ┌────────────────────────────────────────────────┐  │
│  │  ◉  OpenAI API                    Recommended  │  │
│  │                                                │  │
│  │  API Key                                       │  │
│  │  ┌──────────────────────────────────────────┐  │  │
│  │  │ sk-...                              [👁]  │  │  │
│  │  └──────────────────────────────────────────┘  │  │
│  │  Stored securely in macOS Keychain             │  │
│  │                                                │  │
│  │  ✓ Key validated · Model: gpt-4o               │  │
│  └────────────────────────────────────────────────┘  │
```

---

## Screen 3: Onboarding — Context Storage

**Window:** 640×480px

```
┌──────────────────────────────────────────────────────┐
│  ● ● ●                                    2 of 4     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Where Should Your Agent Store Context?              │
│  This is where memories, notes, and files live       │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  ◉  Default Location                          │  │
│  │     ~/Documents/Executive AI/                  │  │
│  │     Simple start, works for most people        │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  ○  Choose Custom Folder                      │  │
│  │     Integrate with your existing file system   │  │
│  │                                                │  │
│  │  ┌──────────────────────────────┐  [ Browse ]  │  │
│  │  │ /Users/denis/Money/          │              │  │
│  │  └──────────────────────────────┘              │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  ○  Connect Existing Runtime                  │  │
│  │     Already using useful-agent CLI? Link it.   │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│                              [ Back ]  [ Continue ]  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**States:**
- Default
- Custom folder selected (path input visible)
- Existing runtime detected (green checkmark)
- Existing runtime not found (warning)

---

## Screen 4: Onboarding — Integrations

**Window:** 640×480px

```
┌──────────────────────────────────────────────────────┐
│  ● ● ●                                    3 of 4     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Connect Your Channels                               │
│  Bring your conversations into one inbox             │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  [🤖]  Telegram Bot              [ Connect ]   │  │
│  │        Chat with your agent from Telegram      │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  [🎙]  Transcripted              [ Connect ]   │  │
│  │        Auto-import meeting transcripts         │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  [📧]  Email (Coming Soon)       [ Notify ]    │  │
│  │        Route emails to your agent              │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  [📅]  Calendar (Coming Soon)    [ Notify ]    │  │
│  │        Agent reads your schedule               │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  [💬]  Web Chat                  Built-in ✓    │  │
│  │        Always available in the app             │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│                          [ Skip All ]  [ Continue ]  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**States:**
- Default
- Connected (green checkmark replaces button)
- Connecting (spinner)
- Error (red text, retry button)

### Sub-screen: Telegram Connect

```
┌──────────────────────────────────────────────────────┐
│  ← Back                                              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Connect Telegram                                    │
│                                                      │
│  1. Open @BotFather in Telegram                      │
│  2. Send /newbot and follow the steps                │
│  3. Paste the bot token below                        │
│                                                      │
│  Bot Token                                           │
│  ┌──────────────────────────────────────────────────┐│
│  │ 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11       ││
│  └──────────────────────────────────────────────────┘│
│                                                      │
│  Allowed User IDs (comma-separated)                  │
│  ┌──────────────────────────────────────────────────┐│
│  │ 123456789                                        ││
│  └──────────────────────────────────────────────────┘│
│                                                      │
│  [ Test Connection ]                                 │
│                                                      │
│  ✓ Bot connected · @my_executive_bot                 │
│                                                      │
│                                     [ Done ]         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Screen 5: Onboarding — Feature Tour

**Window:** 640×500px, carousel

```
┌──────────────────────────────────────────────────────┐
│                                           4 of 4     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │                                                │  │
│  │            [Illustration / Screenshot]         │  │
│  │                                                │  │
│  │          Unified Inbox preview                 │  │
│  │                                                │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│              All Chats, One Place                    │
│                                                      │
│     Telegram, web, and CLI conversations in a        │
│     single inbox. Never lose context again.          │
│                                                      │
│                  ● ○ ○ ○ ○                           │
│                                                      │
│                          [ Skip ]  [ Next → ]        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Tour slides (5):**
1. Unified Inbox — all chats in one place
2. Persistent Memory — agent remembers between sessions
3. Smart Routing — info auto-files to the right place
4. Encrypted Backups — your data is safe
5. You're Ready — CTA to start

---

## Screen 6: Main Chat Interface

**Window:** 1100×700px, resizable, min 800×500

```
┌──────────────────────────────────────────────────────────────────────┐
│  ☰  Executive AI                              🔍   🔔   ⚙️   👤    │
├────────────────┬─────────────────────────────────────────────────────┤
│                │                                                     │
│  PINNED        │  Denis · Telegram                                   │
│                │  ─────────────────────────────────────────────────  │
│  📌 Strategy   │                                                     │
│     Discussion │  👤 Denis · 09:15                                   │
│                │  What's my schedule today and what should I         │
│  RECENT        │  prioritize?                                        │
│                │                                                     │
│  🤖 Telegram   │  🤖 Agent · 09:15                                   │
│    Denis  ●   │  ┌───────────────────────────────────────────────┐  │
│    Alice      │  │ Good morning! Here's your day:               │  │
│                │  │                                               │  │
│    Web Chat   │  │ **Schedule:**                                 │  │
│    New chat   │  │ - 10:00 — Team standup (Zoom)                │  │
│                │  │ - 14:00 — Investor meeting (office)          │  │
│    CLI        │  │ - 16:00 — Product review                     │  │
│    session-1  │  │                                               │  │
│                │  │ **Priority:**                                 │  │
│  ────────────  │  │ Investor meeting prep — the deck needs      │  │
│                │  │ slides 5-8 updated with Q2 numbers.         │  │
│  ARCHIVED      │  │ Want me to draft the updates?               │  │
│                │  └───────────────────────────────────────────────┘  │
│  📁 Q1 Report  │                                                     │
│  📁 Old chats  │  📎 Context used: schedule.md, priorities.md       │
│                │                                                     │
│                │  ┌───────────────────────────────────────────────┐  │
│                │  │ Type a message...              [🎙] [📎] [➤] │  │
│                │  └───────────────────────────────────────────────┘  │
├────────────────┴─────────────────────────────────────────────────────┤
│  Agent: gpt-4o · Context: 12.4K tokens · Last backup: 2h ago       │
└──────────────────────────────────────────────────────────────────────┘
```

### Sidebar Components

**Chat item states:**
- Default
- Selected (blue bg)
- Unread (bold + dot indicator)
- Pinned (pin icon)
- Hover (subtle bg)

**Source icons:**
- 🤖 Telegram
- 💬 Web Chat
- ⌨️ CLI
- 🔌 API

### Chat Message Components

**User message:**
- Right-aligned or left-aligned with avatar
- Editable (click to edit, re-send)
- Timestamp

**Agent message:**
- Left-aligned with bot avatar
- Markdown rendered
- Code blocks with syntax highlighting + copy
- "Context used" indicator (collapsible)
- Actions: Copy, Regenerate, Share

**System message:**
- Centered, muted
- "Chat started", "Telegram connected", etc.

### Input Area
- Auto-growing textarea
- Send button (⌘+Enter or click)
- Voice input button (🎙)
- File attach button (📎)
- Token counter (subtle)

### Status Bar (bottom)
- Active model
- Context token count
- Last backup time
- Connection status

---

## Screen 7: Settings (Browser/WebView)

**Opens in:** Embedded WebView or external browser at `localhost:PORT/settings`

```
┌──────────────────────────────────────────────────────────────────────┐
│  Settings                                         Executive AI Agent │
├────────────────┬─────────────────────────────────────────────────────┤
│                │                                                     │
│  GENERAL       │  General Settings                                   │
│  ● General     │  ─────────────────────────────────────────────────  │
│    AI Provider │                                                     │
│    Context     │  Agent Name                                         │
│    Integrations│  ┌──────────────────────────────────────────────┐   │
│    Backups     │  │ Executive Assistant                          │   │
│    Advanced    │  └──────────────────────────────────────────────┘   │
│                │                                                     │
│                │  Language                                           │
│                │  ┌──────────────────────────────────────────────┐   │
│                │  │ English (US)                            ▼   │   │
│                │  └──────────────────────────────────────────────┘   │
│                │                                                     │
│                │  Theme                                              │
│                │  ○ Light   ● Dark   ○ System                       │
│                │                                                     │
│                │  Notifications                                      │
│                │  [✓] Desktop alerts for new messages                │
│                │  [✓] Sound                                          │
│                │  [ ] Do not disturb (22:00 - 08:00)                │
│                │                                                     │
│                │                              [ Save Changes ]       │
│                │                                                     │
└────────────────┴─────────────────────────────────────────────────────┘
```

### Settings Sections Detail

**AI Provider:**
- Provider dropdown
- API key field (masked, show/hide)
- Model selector
- Temperature slider (0-2)
- Max tokens input
- "Test Connection" button
- Usage chart (tokens/day)

**Context & Memory:**
- Context folder path + "Change" button
- MemPalace embedding model
- Auto-backup toggle + frequency
- "Rebuild Memory Index" button
- Storage usage breakdown

**Integrations:**
- Telegram: connected status, bot username, edit token, disconnect
- Transcripted: connected status, toggle auto-import
- Each integration: card with status + actions

**Backups:**
- Backup location
- Encryption toggle
- Schedule (daily/weekly/manual)
- "Backup Now" button
- Backup history list with restore buttons
- Export all data

**Advanced:**
- Log level dropdown
- Developer mode toggle
- "Open Logs Folder" button
- "Reset to Defaults" button (with confirmation)
- "Uninstall" button (with confirmation)
- App version + check for updates

---

## Screen 8: Menu Bar Popover

**Size:** 280×360px

```
┌────────────────────────────┐
│  🟢 Executive AI Agent     │
│  Running · gpt-4o          │
│  ────────────────────────  │
│                            │
│  ┌──────────────────────┐  │
│  │ 💬  Open Chat        │  │
│  └──────────────────────┘  │
│                            │
│  ┌──────────────────────┐  │
│  │ ⚙️  Settings         │  │
│  └──────────────────────┘  │
│                            │
│  ┌──────────────────────┐  │
│  │ 🔄  Restart Agent    │  │
│  └──────────────────────┘  │
│                            │
│  ────────────────────────  │
│                            │
│  ┌──────────────────────┐  │
│  │ 📦  Backup Now       │  │
│  └──────────────────────┘  │
│                            │
│  ┌──────────────────────┐  │
│  │ 📋  View Logs        │  │
│  └──────────────────────┘  │
│                            │
│  ────────────────────────  │
│                            │
│  ┌──────────────────────┐  │
│  │ ⏻   Quit            │  │
│  └──────────────────────┘  │
│                            │
│  v1.0.0 · Check for updates│
└────────────────────────────┘
```

**Menu bar icon states:**
- 🟢 Green dot: running
- 🟡 Yellow dot: degraded (some services down)
- 🔴 Red dot: stopped
- ⚪ No dot: idle (no recent activity)

---

## Screen 9: Notifications

### Desktop Notification (macOS native)

```
┌──────────────────────────────────────┐
│  🤖 Executive AI                     │
│                                      │
│  New message from Denis (Telegram):  │
│  "Can you prepare the Q2 report?"    │
│                                      │
│  [ Reply ]  [ Open ]                 │
└──────────────────────────────────────┘
```

### In-App Toast

```
┌──────────────────────────────────────┐
│  ✓  Backup completed successfully    │
│                              [ ✕ ]   │
└──────────────────────────────────────┘
```

---

## Interaction Patterns

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `⌘N` | New chat |
| `⌘T` | Focus search |
| `⌘,` | Open settings |
| `⌘K` | Command palette |
| `⌘⇧V` | Voice input |
| `⌘Enter` | Send message |
| `⌘⇧R` | Regenerate response |
| `Esc` | Close modal/popover |

### Transitions
- Onboarding steps: horizontal slide (300ms ease)
- Sidebar expand/collapse: 200ms ease
- Modal appear: fade + scale (200ms)
- Message appear: fade in from bottom (150ms)

### Loading States
- Skeleton screens for chat list
- Spinner for message sending
- Progress bar for backup/restore
- Shimmer for initial context load

---

## Responsive Behavior

### Window Sizes
| Breakpoint | Width | Layout |
|------------|-------|--------|
| Compact | 800-900px | Sidebar collapsed to icons |
| Default | 900-1200px | Sidebar + chat |
| Wide | 1200px+ | Sidebar + chat + context panel |

### Compact Mode (sidebar collapsed)
```
┌──────────────────────────────────────────────────────┐
│  ☰  Executive AI                        🔍  ⚙️  👤  │
├──────┬───────────────────────────────────────────────┤
│      │                                               │
│  🤖  │  Denis · Telegram                             │
│  ●   │  ...                                          │
│      │                                               │
│  💬  │                                               │
│      │                                               │
│  ⌨️  │                                               │
│      │                                               │
├──────┴───────────────────────────────────────────────┤
│  Agent: gpt-4o · 12.4K tokens                       │
└──────────────────────────────────────────────────────┘
```

---

## Assets Needed

### Icons (SF Symbols where possible)
- App icon (1024×1024, all sizes)
- Menu bar icon (16×16, 22×22 template)
- Provider logos: OpenAI, Anthropic, Ollama
- Integration logos: Telegram, Transcripted
- UI icons: chat, settings, backup, search, mic, attach, send

### Illustrations (for onboarding tour)
1. Unified Inbox concept
2. Memory/context persistence
3. Smart routing visualization
4. Backup/security shield
5. "Ready to go" celebration

### App Icon Concept
- Minimal, recognizable at 16px
- Suggests: executive, brain, assistant
- Works in light and dark mode
- Follows macOS Big Sur+ rounded square shape
