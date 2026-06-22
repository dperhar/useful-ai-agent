# Executive AI Agent — User Flow (MECE)

## Overview

Executive AI Agent — desktop-приложение для macOS (Apple Silicon), которое объединяет все каналы коммуникации с AI-агентом в единый интерфейс с онбордингом и настройками.

---

## A. Distribution & Installation

### A1. Download
- **Формат**: DMG с universal binary (Apple Silicon native, Rosetta fallback)
- **Источник**: GitHub Releases / landing page
- **Размер**: ~50MB (без зависимостей)
- **Подпись**: Apple Developer ID + notarization

### A2. Installation
- Drag-and-drop в `/Applications`
- Первый запуск: Gatekeeper bypass через right-click или автоматическая подпись
- Альтернатива: `brew install --cask executive-ai` (future)

### A3. System Requirements
- macOS 13+ (Ventura)
- Apple Silicon (M1/M2/M3/M4) или Intel с Rosetta 2
- 500MB disk space
- Internet connection для LLM API

---

## B. First Launch & Onboarding

### B1. Welcome Screen
```
┌─────────────────────────────────────────┐
│                                         │
│     Executive AI Agent                  │
│     Your personal AI chief of staff     │
│                                         │
│     [ Get Started ]                     │
│                                         │
└─────────────────────────────────────────┘
```

### B2. LLM Provider Setup
**Варианты подключения:**

| Option | Description | User Action |
|--------|-------------|-------------|
| OpenAI API | Direct API key | Вставить API key |
| Opencode Go | Subscription-based | OAuth login |
| Anthropic | Claude API | Вставить API key |
| Local (Ollama) | Self-hosted | Указать endpoint |
| Skip | Настроить позже | Пропустить шаг |

**UI Flow:**
```
┌─────────────────────────────────────────┐
│  Connect Your AI Provider               │
│                                         │
│  ○ OpenAI API (Recommended)             │
│  ○ Opencode Go                          │
│  ○ Anthropic (Claude)                   │
│  ○ Local (Ollama/LM Studio)             │
│  ○ Skip for now                         │
│                                         │
│  [ Continue ]                           │
└─────────────────────────────────────────┘
```

**После выбора:**
- OpenAI/Anthropic: input field для API key → validate → сохранить в Keychain
- Opencode Go: OAuth flow в embedded webview → token в Keychain
- Local: input field для endpoint URL → test connection

### B3. Context Storage Configuration
**Вопрос: Где хранить контекст агента?**

| Option | Path | Use Case |
|--------|------|----------|
| Default | `~/Documents/Executive AI/` | Простой старт |
| Custom | User-selected folder | Интеграция с существующими файлами |
| Existing | Указать путь к useful-agent runtime | Миграция с CLI версии |

**UI Flow:**
```
┌─────────────────────────────────────────┐
│  Where should your agent store context? │
│                                         │
│  [📁 ~/Documents/Executive AI/     ]    │
│                                         │
│  ○ Use default location                 │
│  ○ Choose custom folder                 │
│  ○ Connect existing runtime             │
│                                         │
│  [ Continue ]                           │
└─────────────────────────────────────────┘
```

**После выбора:**
- Создать структуру папок (canon/, active/, archive/, etc.)
- Инициализировать AGENTS.md с базовым роутингом
- Создать CLAUDE.md wrapper

### B4. Feature Tour (Interactive Guide)
**5 экранов с основными фичами:**

1. **Unified Inbox**
   - "Все чаты с агентом в одном месте — Telegram, web, CLI"
   - Screenshot: список чатов

2. **Context Memory**
   - "Агент помнит контекст между сессиями"
   - Screenshot: MemPalace search

3. **Smart Routing**
   - "Информация автоматически попадает в нужные файлы"
   - Screenshot: routing table

4. **Encrypted Backups**
   - "Ваши данные зашифрованы и сохранены"
   - Screenshot: backup settings

5. **Ready!**
   - "Начните с создания первого чата или подключите Telegram"
   - CTA: [Open Chat] [Connect Telegram] [Finish Later]

---

## C. Main Interface — Agentic Chat

### C1. Layout
```
┌────────────────────────────────────────────────────────────────┐
│  ☰  Executive AI                          ⚙️  👤               │
├──────────────┬─────────────────────────────────────────────────┤
│              │                                                 │
│  CHATS       │  Chat Name                                      │
│              │  ─────────────────────────────────────────────  │
│  ● Telegram  │                                                 │
│    Denis     │  User: Привет, что у меня сегодня?              │
│    Alice     │                                                 │
│              │  Agent: Доброе утро! Вот твой план на сегодня:  │
│  ● Web Chat  │  1. 10:00 — созвон с командой                  │
│    New chat  │  2. 14:00 — встреча с инвестором               │
│              │  3. Подготовить отчёт к пятнице                 │
│  ● CLI       │                                                 │
│    session-1 │                                                 │
│              │  ┌─────────────────────────────────────────┐    │
│              │  │ Type a message...                  [➤]  │    │
│              │  └─────────────────────────────────────────┘    │
└──────────────┴─────────────────────────────────────────────────┘
```

### C2. Chat Sources (Unified Inbox)

| Source | Icon | Description |
|--------|------|-------------|
| Telegram | 🤖 | Чаты из Telegram бота (Nanobot) |
| Web Chat | 💬 | Локальный web UI (localhost:port) |
| CLI | ⌨️ | Сессии из терминала |
| API | 🔌 | External integrations (future) |

### C3. Chat Features
- **Markdown rendering** с syntax highlighting
- **Code blocks** с copy button
- **File attachments** (drag & drop)
- **Voice input** (через Transcripted integration)
- **Context indicators** — какие файлы/память использованы
- **Regenerate response** button
- **Edit user message** (re-run with edited input)

### C4. Chat List Features
- **Search** по всем чатам
- **Pin** важные чаты
- **Archive** старые чаты
- **Tags/Labels** для организации
- **Unread indicators** для новых сообщений из Telegram

---

## D. Settings (Browser-Based)

### D1. Settings Access
- **In-app**: ⚙️ icon → opens embedded webview или external browser
- **Direct URL**: `http://localhost:PORT/settings`
- **CLI**: `executive-ai settings`

### D2. Settings Sections

#### D2.1 General
- App name / Agent persona
- Language preference
- Theme (light/dark/system)
- Notifications (desktop alerts for new messages)

#### D2.2 AI Provider
- Active provider selection
- API key management (stored in Keychain)
- Model selection (GPT-4, Claude, etc.)
- Temperature / max tokens
- Usage statistics

#### D2.3 Context & Memory
- Context folder location
- MemPalace settings (embedding model, search limits)
- Auto-backup frequency
- Memory reconciliation schedule

#### D2.4 Integrations
- **Telegram**: bot token, allowed users, webhook settings
- **Transcripted**: MCP endpoint, auto-import toggle
- **Browser extension**: (future) context bridge

#### D2.5 Backups & Security
- Backup location (local/iCloud/NAS)
- Encryption password (Keychain)
- Backup schedule
- Restore from backup
- Export all data

#### D2.6 Advanced
- Log level
- Developer mode
- Reset to defaults
- Uninstall

---

## E. Background Services

### E1. Menu Bar (Native)
- Agent status (running/stopped)
- Quick actions: Start/Stop/Restart
- Open main window
- Open settings
- Check for updates

### E2. System Integration
- **LaunchAgent**: auto-start on login (optional)
- **Notifications**: native macOS notifications for new messages
- **Spotlight**: (future) index context files for system search

### E3. Background Processes
- Nanobot gateway (Telegram bridge + LLM proxy)
- WebSocket server (local API)
- MemPalace MCP server
- Backup scheduler

### E4. Data Flow Architecture

```
┌─────────────────┐
│  Desktop App    │
│  (Swift+WebView)│
└────────┬────────┘
         │ WebSocket
         ↓
┌─────────────────┐
│    Nanobot      │
│  (LLM Gateway)  │
└────────┬────────┘
         │
    ┌────┴────┬────────┬──────────┐
    ↓         ↓        ↓          ↓
┌────────┐ ┌──────┐ ┌────────┐ ┌──────┐
│ SQLite │ │ LLM  │ │MemPalace│ │Files │
│(chats) │ │ API  │ │(semantic)│ │(SoT) │
└────────┘ └──────┘ └────────┘ └──────┘
```

**Storage layers:**
- **SQLite**: Chat history (fast, indexed, paginated)
- **MemPalace**: Semantic retrieval (important facts, decisions)
- **Markdown files**: Source of truth (strategy, priorities, etc.)
- **Keychain**: API keys, secrets

---

## F. User Journeys

### F1. First-Time User
```
Download DMG → Install → Launch → Welcome Screen → 
Connect LLM Provider → Choose Context Location → 
Feature Tour → Main Chat Interface → 
(Optional) Connect Telegram → First conversation
```

### F2. Existing useful-agent User
```
Download DMG → Install → Launch → Welcome Screen → 
"Connect existing runtime" → Select runtime folder → 
Auto-detect settings → Main Chat Interface → 
See all existing Telegram chats in unified inbox
```

### F3. Daily Usage
```
Menu bar → Open app → See unread messages → 
Reply in unified inbox → Agent uses context from MemPalace → 
Agent writes to source-of-truth files → 
Auto-backup runs in background
```

---

## G. Technical Decisions

### G1. Desktop Framework: Swift + WebView ✓

**Architecture:**
- **Shell**: SwiftUI native macOS app
- **UI rendering**: WKWebView (React/TypeScript frontend)
- **Bridge**: `WKScriptMessageHandler` для native ↔ web коммуникации
- **Menu bar**: NSStatusItem (native)
- **Settings**: WebView window или external browser

**Pros:**
- Minimal bundle size (~15-20MB)
- Native macOS feel и performance
- Direct access к Keychain, NSStatusItem, LaunchAgent
- No Electron overhead

**Cons:**
- macOS only (no Windows/Linux)
- Requires Swift + web dev skills

### G2. Frontend Stack (inside WKWebView)
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS + CSS variables (theme)
- **State**: Zustand
- **Chat UI**: Custom components
- **Build**: Vite → static bundle embedded in app

### G3. Native Layer (Swift)
- `AppDelegate` + `NSStatusItem` для menu bar
- `WKWebView` с `WKScriptMessageHandler` bridge
- Keychain access для API keys
- File system operations
- LaunchAgent management
- Nanobot/WebSocket process management

---

## H. MVP Scope (v1.0)

### Must Have
- [ ] DMG installer с notarization
- [ ] Onboarding: LLM provider setup
- [ ] Onboarding: Context folder selection
- [ ] Unified chat inbox (Telegram + Web)
- [ ] Basic chat UI с markdown
- [ ] Settings page (browser)
- [ ] Menu bar app
- [ ] Integration с existing useful-agent runtime

### Should Have
- [ ] Feature tour
- [ ] Chat search
- [ ] Voice input (Transcripted)
- [ ] Encrypted backups UI

### Nice to Have
- [ ] CLI integration в UI
- [ ] Chat tags/labels
- [ ] Multi-provider support (switch between OpenAI/Claude)
- [ ] Browser extension

---

## I. Open Questions

1. **Branding**: "Executive AI Agent" или другое название?
2. **Pricing**: Free / Freemium / Subscription?
3. **Distribution**: GitHub only или также website?
4. **Analytics**: Собираем ли анонимную телеметрию?
5. **Multi-user**: Один Mac = один пользователь?
6. **Offline mode**: Что делать без интернета? (queue messages, local model fallback?)

---

## Next Steps

1. **Validate user flow** — обсудить этот документ
2. **Choose tech stack** — Tauri vs Electron vs Swift
3. **Design mockups** — Figma для key screens
4. **Scaffold project** — создать Tauri app структуру
5. **Build MVP** — onboarding + basic chat
