# Context Architecture for AI Agents – Reference Guide

> Source: March 2026 field notes on context architecture for AI agents. Condensed for general use.
> This file is reference material for the `context-architecture-setup` skill.

**This folder contains a complete context architecture toolkit:**
- `Context Architecture.md` (this file) – principles and theory. Read first.
- `context-architecture-setup/SKILL.md` – initial setup procedure (Phase 1-4)
- `context-architecture-cleanup/SKILL.md` – quarterly maintenance audit
- `improve/SKILL.md` – output quality control + file reconciliation

---

## Core Thesis

Agent quality = f(context quality), not f(model quality). Same model, same task, better context preparation → +10.6% on benchmarks (Microsoft ACE research). Switching from GPT-4 to Opus won't fix an agent reading 167K tokens of garbage. Fixing what the agent reads will.

"Context is a budget. Spend it like rent money, not casino chips."

---

## The Problem

Agents make bad decisions not because models are weak, but because:
1. **Context Collapse** – quality drops non-linearly with irrelevant context growth. Not "a little worse" – sharply worse after a threshold.
2. **Brevity Bias** – model prefers short/shallow answers when context is overloaded.
3. **Statelessness** – agents don't remember between sessions. Their only "memory" is file structure. If files are chaos, every session starts from zero.

Symptom: codebase looks like 50 slightly different developers wrote it. Each session = new style, new conventions, new decisions. (clawsouls.ai described this as loss of "persistent identity" across sessions.)

---

## 6 Principles

### 1. Context needs architecture, not a pile
Not "one docs/ folder" – layers with different depth and update frequency. Strategic docs update quarterly. Tasks update daily. Canonical data weekly. If they live together, agent wastes tokens on everything.

### 2. Raw data is weak context
Transcripts, metric dumps, draft reports = raw. Agent benefits when data is filtered, normalized, and packaged for the task. One prepared JSON feeds agents better than ten raw exports.

### 3. Each layer needs its own derivative format
Strategy layer needs: patterns, risks, dynamics. Execution layer needs: specific task + constraints + "done" criteria. A monthly competitor analysis and a today's bug fix cannot share the same format. One representation for everything = soup.

### 4. Routing matters more than storage
The problem isn't "where to store." It's: what goes where, what must NOT go somewhere, what enters long-term memory, what stays noise. Describing "what goes where" in CLAUDE.md is more valuable than creating a beautiful hierarchy without rules.

### 5. Goal = decision quality, not task throughput
Agent makes strategically correct decisions more often. Notices weak signals and error repeats because it reads only canon instead of 66 files. Less noise → fewer mistakes.

### 6. Whoever manages context wins
Not who accumulated more data. Who built architecture earlier, learned to filter, and serves the right representation to the right layer at the right moment.

---

## 8 Layers of Context

Each layer has its own speed of change:

| Layer | Examples | Update frequency |
|-------|----------|-----------------|
| Strategy | Mission, vision, principles, org structure | Quarterly |
| Architecture | System design, data models, API contracts | Monthly |
| Canon | Canonical data files, master references | Weekly-Monthly |
| Coordination | Sprint goals, priorities, assignments | Weekly |
| Execution | Current tasks, issue details, PR context | Daily |
| Artifact | Build outputs, test results, deploy logs | Per-deploy |
| Research | Competitor analysis, market data, benchmarks | On-demand |
| Archive | Completed work, historical decisions | Never (read-only) |

When everything is in one folder, agent sees all layers as equally relevant. Strategy.md and a week-old task file are treated as equal-weight documents.

### 5-Layer Adaptation (non-code organizations)

**For business knowledge and product teams** – 8 layers collapse to 5:

| Layer | Maps to | Update speed | Agent reads... |
|-------|---------|-------------|----------------|
| **Canon** | Strategy + Architecture | Quarterly | Always – on every startup |
| **Reference** | Canon + Research | Monthly | When working on that topic |
| **Active** | Coordination | Weekly | When planning or coordinating |
| **Volatile** | Execution + Artifact | Daily | Only for current task |
| **Archive** | Archive | Never (read-only) | Only when explicitly asked |

Use whichever granularity fits the workspace. The principle (group by speed of change) matters more than the exact number of layers. See `context-architecture-setup/SKILL.md` Phase 1, Step 2 for implementation details.

---

## Lifecycle-Split Method

**Principle: organize by speed of change, not by topic.**

Each folder = one-two layers. Each layer = one update frequency.

### Before (typical mess):
```
ROOT (46K tokens, 28% of all context)
strategy.md  systems.md  departments.md
advisor-*.md  research-*.md  plan-*.md
task-*.md  draft-*.md  old-*.md
→ everything in one pile
```

### After (lifecycle-split):
```
ROOT (canon only) ← updates: quarterly, agent reads ALWAYS
├── strategy.md
├── systems.md
├── registry.md
├── CLAUDE.md
│
├── product/     ← updates: monthly (rare)
├── ops/         ← updates: bi-weekly
├── work/        ← updates: daily (tasks tied to issues)
└── archive/     ← updates: never (read-only)
```

**Result:** Root went from 46K to 20K tokens. 42 of 66 files were ballast (23 outdated artifacts, 11 research files that belonged elsewhere, 8 task files without issue references). Agent started making better decisions without model change.

**Audit technique:** For large workspaces (50+ files), use parallel subagents – one per folder or file cluster. One field implementation used 4 subagents simultaneously, each checking a different slice (root, docs/, research+competitors, app+archive). All 66 files were audited in one session.

### Business org example (5-layer adaptation):
```
BEFORE: flat folder, 300K+ tokens, 60%+ noise
  strategy.md  old-notes.md  chat-export.md
  client-a.md  landing-page-code.md  random-prompts.md
  → agent reads everything on startup

AFTER: lifecycle-split, ~150K tokens
ROOT/
├── strategy.md          ← canon
├── AGENTS.md            ← entry point + routing
├── clients/             ← reference (one file per client)
├── projects/            ← active (current work)
└── deprecated/          ← archive (agent ignores unless asked)
```

Same principle, different folder names. Agent reads canon only by default.

---

## Entry Points and Routing

### AGENTS.md (standard)
- 60K+ repos use it. Linux Foundation backed. 20+ tools read natively (Codex, Copilot, Gemini CLI, Windsurf, Cline, Aider, JetBrains Junie).
- One file in repo root. Describes: architectural principles, naming conventions, forbidden patterns, workflows, boundaries.
- What works: canonical paths, boundaries (can/must-confirm/forbidden), source of truth declarations, safe defaults.
- What doesn't work: abstract principles ("write clean code"), walls of text, duplicating rules across sections.

### CLAUDE.md (Claude Code/Cowork)
- Thin wrapper pattern: CLAUDE.md → points to AGENTS.md + Claude-specific rules only.
- No duplication. All canonical content in AGENTS.md. CLAUDE.md adds only tool-specific instructions.
- **Short > long.** One field implementation cut an entry point from 800 to 150 lines and saw higher agent compliance. vibemeta.app independently reported the same direction of effect (847→127 lines). Fewer rules → higher compliance.
- Claude Code does NOT read AGENTS.md natively – it reads CLAUDE.md. The thin wrapper solves this without duplication.

### .cursor/rules (Cursor)
- Another thin wrapper pointing to AGENTS.md.

### Routing table (most valuable content)
Not "where things are" but "what goes where and what's forbidden":
```
1. New strategy input → append to strategy.md
2. New task → create in work/ with issue reference
3. Research output → research/ (never root)
4. Nothing fits → ASK. Do NOT create new file.
```

---

## Operational Rules

Field-tested rules from setting up context architectures in real organizations. These are not optional – agents MUST follow them:

### Timeline convention for knowledge files
- **Top overrides bottom.** Most current data goes ABOVE the last `---`, with timestamp. Agent reads top-to-bottom, so the freshest state should be first.
- New data is added above the previous `---` divider. Older sections stay below – they're history the agent can reference if needed.
- **Exception: STRATEGY DECISIONS update in place** with timestamp (don't scatter same decision across 3 sections). Find the original section, update it, leave a one-line version note.
- Never delete old sections – future agents need the timeline to understand why things changed.
- **Either direction works** (top-overrides-bottom or bottom-overrides-top), but the convention MUST be explicitly stated at the top of every timeline file. Ambiguity here = guaranteed confusion for agents.

### File creation is a controlled operation
- New file = new node in the dependency graph. Every file adds maintenance cost.
- Routing table is the gatekeeper. If the routing table doesn't have a rule for this content → ASK, don't create.
- Rule of thumb: if you can append to an existing file, always prefer that over creating a new one.

### Single source of truth per topic
- If two files describe the same thing, one is wrong (or will be soon).
- When conflict found → update canonical source, make the other a pointer.
- Pointer format: "See [file.md] §section for current state."

### The "new agent" test
- Drop a fresh agent into the folder. No conversation history. Can it find what it needs and do the right thing?
- If no → entry points are broken, routing is missing, or cross-references are dead.

### External input routing (cross-cutting rule)
Every interaction with the outside world – client calls, investor meetings, user interviews, support tickets – generates raw material: quotes, objections, feature requests, market signals. This material has a home in the architecture. The rule is simple:

1. **Identify the canonical file** for that source. Client said it? → client file. User said it? → user research section. Investor said it? → fundraise file.
2. **Append to that file** with timestamp and source attribution. Don't create a new file for each conversation.
3. **If no canonical file exists for that source type** → add a routing rule first, then append. Never let raw input float without a home.

Why this matters: unrouted external input is the #1 cause of file sprawl. One "quick note" becomes a standalone .md, then ten standalone .mds, then the agent reads all of them on every startup and context collapses.

---

## Implementation & Maintenance

**Initial setup:** `context-architecture-setup/SKILL.md` – phases, checklists, time estimates.

**Reactive maintenance (every /improve pass):** `/improve` skill Part 2 (reconciliation) feeds findings back into files per routing table. Keeps individual files current.

**Proactive maintenance (quarterly):** `context-architecture-cleanup/SKILL.md` – audits the architecture itself. Checks: token count drift, orphan files, routing compliance, "new agent" test. Run quarterly or when agent quality noticeably drops.

**After any strategy change:** run /improve reconciliation immediately. Don't wait for the quarterly cleanup.

---

## Key Metrics

- **Root token count** – should decrease or stay stable over time. If growing, context is bloating.
- **"New agent" test pass rate** – fresh agent can complete task without human hints? Higher = better architecture.
- **File creation rate** – how many new files per month? Should be near-zero if routing table works.
- **Orphan file count** – files with zero inbound references. Should be zero outside archive/.
- **Cross-reference accuracy** – % of file references that resolve to existing files. Should be 100%.
