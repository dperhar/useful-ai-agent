# Context Routing — Detailed Specification

## Overview

Context routing — это механизм, который определяет, **куда** агент должен записать информацию из чата. Не "всё в одну папку", а "каждое сообщение в правильное место".

---

## Core Principle

**Routing > Storage**

Проблема не "где хранить", а:
- Что куда идёт
- Что **НЕ** должно куда-то идти
- Что попадает в long-term memory
- Что остаётся noise

---

## Routing Table

### Location: `AGENTS.md` (root of context folder)

```markdown
# Routing Table

## Strategy Layer (updates: quarterly)
- **strategy.md** — Mission, vision, principles, org structure
- **systems.md** — Internal systems, tools, processes
- **departments.md** — Team structure, roles, responsibilities

**Route here when:**
- User discusses company direction, values, culture
- User mentions organizational changes
- User defines principles or policies

## Active Layer (updates: daily)
- **priorities.md** — Current priorities, goals, OKRs
- **schedule.md** — Calendar, meetings, deadlines
- **projects/[name].md** — Project-specific context

**Route here when:**
- User mentions tasks, deadlines, meetings
- User discusses project status, blockers
- User sets goals or priorities

## Reference Layer (updates: monthly)
- **clients/[name].md** — Client information, history
- **research/[topic].md** — Market research, competitors
- **decisions.md** — Important decisions with rationale

**Route here when:**
- User shares client feedback, quotes
- User discusses market, competitors
- User makes important decisions

## Archive Layer (updates: never)
- **archive/[year]/[month].md** — Completed work, old context

**Route here when:**
- Project completed
- Priority no longer relevant
- User explicitly says "archive this"

## Chat History (updates: always)
- **SQLite database** — All messages
- **MemPalace** — Important facts, decisions (semantic index)

**Route here when:**
- Every message (SQLite)
- Important facts, decisions (MemPalace)
```

---

## Routing Decision Flow

```
User sends message
       ↓
Agent analyzes message
       ↓
┌──────────────────────────────────────┐
│  Does this contain actionable info?  │
└──────────────────────────────────────┘
       ↓                    ↓
      YES                   NO
       ↓                    ↓
┌──────────────┐    ┌────────────────┐
│ What type?   │    │ Store in chat  │
│              │    │ history only   │
│ - Decision   │    │ (SQLite)       │
│ - Task       │    └────────────────┘
│ - Fact       │
│ - Meeting    │
│ - Priority   │
│ - Client     │
└──────────────┘
       ↓
┌──────────────────────────────────────┐
│  Match to routing table              │
│  - Decision → decisions.md           │
│  - Task → priorities.md              │
│  - Meeting → schedule.md             │
│  - Client → clients/[name].md        │
│  - Priority → priorities.md          │
│  - Fact → MemPalace + relevant file  │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│  Append to file with:                │
│  - Timestamp                         │
│  - Source attribution                │
│  - Context (if needed)               │
└──────────────────────────────────────┘
       ↓
┌──────────────────────────────────────┐
│  Index in MemPalace (if important)   │
└──────────────────────────────────────┘
```

---

## Routing Examples

### Example 1: Meeting Mention

**User:** "Завтра в 14:00 встреча с инвестором, нужно подготовить deck"

**Agent routing:**
1. **schedule.md** — Add meeting: "14:00 — Investor meeting"
2. **priorities.md** — Add task: "Prepare investor deck"
3. **SQLite** — Store message
4. **MemPalace** — Index: "Investor meeting tomorrow at 14:00, need deck"

**Agent response:**
"Добавил в расписание: завтра в 14:00 встреча с инвестором. Также добавил задачу — подготовить deck. Хочешь, чтобы я помог с презентацией?"

---

### Example 2: Strategic Decision

**User:** "Решили, что с Q3 фокусируемся на enterprise сегменте, SMB пока на паузе"

**Agent routing:**
1. **strategy.md** — Update strategy section: "Q3 focus: enterprise segment, SMB on hold"
2. **decisions.md** — Add decision with rationale
3. **SQLite** — Store message
4. **MemPalace** — Index: "Strategic decision: focus on enterprise from Q3, SMB paused"

**Agent response:**
"Записал: с Q3 фокус на enterprise, SMB на паузе. Добавил в strategy.md и decisions.md. Хочешь обсудить, как это повлияет на текущие проекты?"

---

### Example 3: Client Feedback

**User:** "Клиент из Acme Corp сказал, что им не хватает интеграции с Salesforce"

**Agent routing:**
1. **clients/acme-corp.md** — Add feedback: "Needs Salesforce integration"
2. **SQLite** — Store message
3. **MemPalace** — Index: "Acme Corp feedback: missing Salesforce integration"

**Agent response:**
"Записал: Acme Corp нужна интеграция с Salesforce. Это фича-реквест или blocker для сделки?"

---

### Example 4: Casual Chat (No Routing)

**User:** "Привет, как дела?"

**Agent routing:**
1. **SQLite** — Store message (chat history only)
2. **No file updates** — No actionable information

**Agent response:**
"Привет! Всё отлично, готов помогать. Что у тебя на повестке?"

---

## Routing Rules

### Rule 1: Append, Don't Replace

**Wrong:**
```markdown
## Priorities
- Prepare investor deck
```

**Right:**
```markdown
## Priorities

---
2026-06-22 14:30 · from Telegram
- Prepare investor deck (deadline: tomorrow 14:00)

---
2026-06-20 10:00 · from Web
- Finish Q2 report
- Review team OKRs
```

**Why:** Timeline convention — top overrides bottom, history preserved.

---

### Rule 2: Single Source of Truth

**Wrong:**
- priorities.md: "Prepare investor deck"
- tasks.md: "Prepare investor deck"
- notes.md: "Investor deck TODO"

**Right:**
- priorities.md: "Prepare investor deck"
- Other files: "See priorities.md for current tasks"

**Why:** If two files describe the same thing, one is wrong.

---

### Rule 3: Ask When Uncertain

**Scenario:** User says something ambiguous.

**Agent should:**
1. Check routing table
2. If no clear match → ASK
3. Don't create new file without permission

**Example:**
**User:** "Нужно разобраться с той штукой"

**Agent:** "Уточни, пожалуйста: это задача, вопрос для исследования, или что-то ещё? И о какой 'штуке' речь?"

---

### Rule 4: External Input Routing

**Every interaction with outside world → route to canonical file:**

| Source | Route to |
|--------|----------|
| Client call | clients/[name].md |
| User interview | research/users.md |
| Investor meeting | fundraise.md |
| Support ticket | support/[issue].md |
| Competitor news | research/competitors.md |

**Format:**
```markdown
---
2026-06-22 15:00 · Client call with Acme Corp
- They need Salesforce integration
- Deal size: $50K ARR
- Decision expected: July 15
```

---

### Rule 5: Strategy Decisions Update In Place

**Wrong:**
```markdown
## Strategy

---
2026-06-22
- Focus on enterprise

---
2026-03-15
- Focus on SMB
```

**Right:**
```markdown
## Strategy

### Target Segment
**Current (2026-06-22):** Enterprise segment
**Previous (2026-03-15):** SMB segment (paused Q3)

*Updated: 2026-06-22 — shifted focus based on market feedback*
```

**Why:** Strategy decisions update in place with timestamp, not scattered across timeline.

---

## Conflict Resolution

### Conflict 1: Multiple Routing Targets

**Scenario:** Message could go to multiple files.

**User:** "Завтра встреча с Acme Corp, нужно обсудить pricing"

**Options:**
- schedule.md (meeting)
- clients/acme-corp.md (client interaction)
- pricing.md (pricing discussion)

**Resolution:**
1. **Primary:** schedule.md (meeting is time-bound)
2. **Secondary:** clients/acme-corp.md (client context)
3. **Skip:** pricing.md (no pricing decision yet)

**Agent response:**
"Добавил в расписание: завтра встреча с Acme Corp. Также добавил заметку в карточку клиента. Когда будет решение по pricing — запишем отдельно."

---

### Conflict 2: Contradiction with Existing Data

**Scenario:** New information contradicts existing file.

**Existing (priorities.md):**
```markdown
- Launch feature X by June 30
```

**User:** "Решили перенести запуск feature X на август"

**Resolution:**
1. Update priorities.md with new date
2. Add note about change
3. Index in MemPalace

**Updated (priorities.md):**
```markdown
- Launch feature X by August 31
  *Changed: 2026-06-22 — moved from June 30 due to scope expansion*
```

---

### Conflict 3: User Disagrees with Routing

**Scenario:** Agent routes to wrong file.

**User:** "Нет, это не задача, это просто мысль"

**Resolution:**
1. Remove from priorities.md
2. Store in chat history only (or notes.md if exists)
3. Learn from feedback (future: better classification)

**Agent response:**
"Понял, убрал из задач. Оставлю в истории чата. Если захочешь вернуться к этой мысли — скажи."

---

## Desktop App Integration

### UI: Routing Indicators

**When agent writes to file:**

```
┌─────────────────────────────────────────┐
│ 🤖 Agent                                │
│                                         │
│ Записал:                                │
│ 📄 strategy.md — обновил фокус          │
│ 📄 decisions.md — добавил решение       │
│ 🧠 MemPalace — проиндексировал          │
│                                         │
│ [ View files ]  [ Undo ]                │
└─────────────────────────────────────────┘
```

**User actions:**
- **View files** — Open files in Finder/editor
- **Undo** — Revert changes (remove appended text)

---

### UI: Manual Routing

**User can explicitly route:**

```
┌─────────────────────────────────────────┐
│ 👤 User                                 │
│                                         │
│ Запомни: мы решили использовать Tauri   │
│ [ 📎 Route to... ]                      │
└─────────────────────────────────────────┘
```

**Click "Route to..." → dropdown:**
- strategy.md
- decisions.md
- priorities.md
- Custom file...

---

### UI: Routing Settings

**In Settings → Context:**

```
┌─────────────────────────────────────────┐
│  Routing Rules                          │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ Auto-route decisions         [✓] │  │
│  │ Auto-route tasks             [✓] │  │
│  │ Auto-route meetings          [✓] │  │
│  │ Ask before routing           [ ] │  │
│  └───────────────────────────────────┘  │
│                                         │
│  [ Edit routing table (AGENTS.md) ]     │
│                                         │
└─────────────────────────────────────────┘
```

---

## MemPalace Integration

### When to Index in MemPalace

**Always index:**
- Decisions ("We decided to use Tauri")
- Facts ("Investor meeting is on Friday")
- Preferences ("I prefer dark mode")
- Deadlines ("Report due June 30")
- Important quotes (client feedback)

**Never index:**
- Greetings ("Hi", "Thanks")
- Acknowledgments ("Got it", "OK")
- Small talk ("How are you?")
- Transient questions ("What time is it?")

**Index with caution:**
- Questions (only if important: "Why did we choose X?")
- Hypotheticals (only if likely to become real)
- Jokes (never, unless user says "remember this")

---

### MemPalace Drawer Format

**Decision:**
```
DECISION:2026-06-22|chose.Tauri.over.Electron+Swift.WebView|REASON:smaller.bundle.native.feel|★★★
```

**Fact:**
```
FACT:2026-06-22|investor.meeting.scheduled.2026-06-23.14:00|PREP:deck.slides.5-8.update|★★★
```

**Preference:**
```
PREF:ui.theme|dark.mode.preferred|★★
```

---

### Retrieval Flow

**User asks:** "Что мы решили по поводу фреймворка?"

**Agent:**
1. MemPalace search: "framework decision"
2. Find: `DECISION:2026-06-22|chose.Tauri...`
3. Response: "Мы решили использовать Tauri (Swift + WebView). Причина: меньший размер бандла и native feel."

---

## Routing Table Maintenance

### Quarterly Audit

**Check:**
1. Are files being updated correctly?
2. Any orphan files (no inbound routes)?
3. Any routing conflicts?
4. Is routing table still accurate?

**Actions:**
- Update routing table if needed
- Archive unused files
- Resolve conflicts

---

### User Feedback Loop

**When user corrects routing:**
1. Log the correction
2. Adjust future routing decisions
3. (Future) ML model for better classification

**Example:**
- User: "Это не задача, это вопрос для исследования"
- Agent: Logs correction, routes to research/ instead of priorities.md
- Future: Similar messages routed to research/

---

## Open Questions

1. **Routing confidence:** Should agent show confidence level? ("80% sure this goes to priorities.md")
2. **Batch routing:** Route each message immediately, or batch at end of conversation?
3. **Routing history:** Keep log of all routing decisions for audit?
4. **Multi-language:** How to handle routing when user switches languages?
5. **Ambiguity threshold:** When to ask vs when to guess?

---

## Summary

**Context routing = intelligent filing system**

- Every message analyzed for actionable information
- Routed to correct file based on routing table
- Appended with timestamp and attribution
- Indexed in MemPalace if important
- User can view, undo, or manually route

**Key files:**
- `AGENTS.md` — Routing table (source of truth)
- `strategy.md`, `priorities.md`, etc. — Routed content
- SQLite — Chat history (all messages)
- MemPalace — Semantic index (important facts)

**Desktop app features:**
- Routing indicators (what files updated)
- Manual routing (user chooses file)
- Undo routing (revert changes)
- Routing settings (auto vs manual)
