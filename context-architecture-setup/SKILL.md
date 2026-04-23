---
name: context-architecture-setup
description: |
  Set up a lean, navigable context architecture for AI agents in an organization. Guides the agent through assessment, design, implementation, and verification of lifecycle-split file structure, routing rules, and entry points (CLAUDE.md / AGENTS.md). Use when: a team needs their AI agents to stop hallucinating and start making better decisions, the workspace is messy, or the user wants to set up context for Claude Code / Cursor / Copilot / any AI tool. Trigger on: "set up context", "context architecture", "AI enablement", "agent setup", "file structure for AI", "agent keeps losing context", "agent hallucinating", "set up CLAUDE.md", "set up AGENTS.md".
---

# Context Architecture Setup

> Reference material: `Context Architecture.md` (same folder). Read it for principles and theory.
> Quality control: `improve/SKILL.md` (same folder). Use it for polishing outputs and maintaining file hygiene.

## What This Skill Does

Sets up a context architecture so AI agents in a client organization:
- Read only what they need (no 167K token noise)
- Know where to find information (routing, not hunting)
- Know where to PUT new information (file creation rules)
- Don't create file sprawl (controlled file creation)
- Remember decisions between sessions (structured persistence)
- Can be replaced by a fresh agent and still work (the "new agent" test)

## Starting Conditions

This skill handles three scenarios. Identify which one applies before starting:

### Scenario A: No harness ("we just started using AI tools")
- No AGENTS.md, no CLAUDE.md, no .cursor/rules
- Files might be organized by topic (projects/, docs/, notes/) or not organized at all
- Context may live outside the file system entirely: in Telegram chats, browser tabs, Google Docs, Notion, email threads
- Agent reads everything on startup or has nothing to read
- **→ Start at Phase 1, Step 1. Build from scratch.**

### Scenario B: Messy harness ("we have some setup but it's chaos")
- Entry point may exist but is bloated (300+ lines), outdated, or contradicts itself
- Files scattered across folders with no lifecycle logic
- No routing table → agents create files wherever they want
- Multiple sources of truth for the same topic
- Context leaks: important information trapped in chat histories, unstructured notes, random .md files
- **→ Start at Phase 1, Step 1. Treat as a fresh assessment – existing harness may need rebuilding.**

**Decommission step (Scenario B only):** Before building new architecture, neutralize the old entry point so the agent doesn't read it on startup. Rename `CLAUDE.md` → `CLAUDE.md.old` (or move to archive/). Same for `.cursor/rules` or any tool-specific config that auto-loads. Archive first, build new second. Otherwise the agent reads the OLD bloated entry point and ignores the new one.

### Scenario C: Existing clean harness ("we did setup, need a refresh")
- Architecture exists and mostly works but has drifted
- Token count grew, some routing violations, some orphan files
- **→ Use `context-architecture-cleanup/SKILL.md` instead. This skill is for initial setup.**

## Client Brief

> Share this section with the operator (or explain verbally) before starting the work. It explains what's about to happen in plain language. Match the user's language.

**What we're doing:** Organizing your workspace so AI agents (Claude, Cursor, Copilot – whatever you use) make better decisions. Right now, your agent either has very little context, or worse –  reads everything on startup – strategy docs, old drafts, task lists, archived reports – and treats them all as equally important. That's why it gives shallow answers or contradicts itself between sessions.

**How it works:**
1. **Assessment (~1.5h):** We map every file your agents can see, classify them by how fast they change, and find problems – duplicates, outdated files, missing connections.
2. **Design (~1.5h):** We design a folder structure grouped by speed of change (strategy files separate from daily tasks) and create routing rules (where does new information go).
3. **Implementation (~2h):** We create the entry point files, move files to their correct locations, eliminate duplicates, and set up rules that prevent future mess.
4. **Verification (~1h):** We test by starting a fresh AI session to see if a new agent can navigate without help.

**What you get:**
- Entry point file (AGENTS.md or CLAUDE.md) with routing table – installed
- Lifecycle-split folder structure – implemented
- Two maintenance skills: `/improve` (keeps files accurate) and `/context-architecture-cleanup` (quarterly health check)
- "New agent" test results – baseline for measuring drift

**Nothing gets deleted.** Outdated files move to an archive folder. Your agent ignores them unless you specifically ask.

**Expected result:** Same AI model, noticeably better decisions. Microsoft research showed +10.6% quality improvement from better context preparation alone – no model change needed.

## Phase 1: Assessment

### Step 1: Map current state

Ask the client (or explore their workspace):
1. Where do your AI agents currently read context from? (folder, files, config)
2. How many files are in the root / main context folder?
3. What does the agent see on startup? (auto-loaded files, CLAUDE.md, etc.)
4. How often do these files change? (daily? monthly? never?)
5. Where does important context live OUTSIDE the file system? (chat histories, cloud docs, browser tabs, email threads, Notion/Confluence, Telegram channels)

For question 5: context trapped outside the workspace is invisible to agents. During assessment, identify these sources and plan to extract key information into the file system. Don't try to import everything – extract only decisions, constraints, and facts that agents need to act on.

**For large workspaces (50+ files):** use parallel subagents – one per folder or file cluster. Example: 4 subagents simultaneously, each auditing a different slice (root files, docs/, research/, app+config). All files assessed in one session instead of sequential crawling.

**Token counting method:** Use `wc -c *.md | tail -1` and divide by 4 for a rough token estimate. For more precision: `cat *.md | wc -w` gives word count; tokens ≈ words × 1.3. Exact tokenizers exist but overkill for assessment.

### Step 2: Classify files by lifecycle

For each file, determine its layer:

| Layer | Update speed | Examples |
|-------|-------------|----------|
| **Canon** | Quarterly | Strategy, principles, org structure, architecture |
| **Reference** | Monthly | Product specs, API contracts, competitor landscape |
| **Active** | Weekly | Sprint goals, priorities, current projects |
| **Volatile** | Daily | Tasks, drafts, conversation logs |
| **Archive** | Never | Completed work, old decisions (read-only) |

**Raw data is not ready context.** Transcripts, metric dumps, chat exports, raw API responses – these are raw material, not files an agent should read. During classification, flag raw data files separately. They need EXTRACTION (pull out decisions, constraints, facts) before they belong in any layer. Don't classify a chat transcript as "volatile" and move it to work/ – extract what matters, route the extracted content per the routing table, archive or delete the raw source.

**Layer format check:** Each layer has its own format needs. Strategy files should contain patterns, risks, dynamics – not raw meeting notes. Task files should contain: specific task + constraints + "done" criteria – not stream-of-consciousness planning. If a file is in the right layer but wrong format, flag it for rewriting during Phase 3.

### Step 3: Find problems

- **Bloat**: count tokens in root. Over 20K? Too fat.
- **Duplicates**: same topic in 2+ files → guaranteed divergence
- **Orphans**: files with zero inbound references → noise
- **Ghosts**: references pointing to files that don't exist → broken navigation
- **Mixed lifecycle**: canon + volatile in same folder → agent can't tell what's fresh

Present findings to client as a simple table: file, current location, lifecycle layer, problem (if any).

**Benchmark:** In a real 66-file workspace audit, 42 files (64%) were ballast – 23 outdated artifacts, 11 research files that belonged in a subfolder, 8 task files without issue references. Expect similar ratios. If less than 30% of files are ballast, the workspace is already cleaner than average.

## Phase 2: Design

### Step 4: Design folder structure (lifecycle-split)

One folder per lifecycle speed:
```
ROOT/ (canon only – agent reads ALWAYS)
├── CLAUDE.md or AGENTS.md (entry point + routing)
├── strategy.md (or equivalent)
├── [2-5 other canonical files]
│
├── reference/    (monthly updates)
├── active/       (weekly updates)
├── work/         (daily – tasks tied to issues)
└── archive/      (read-only, agent ignores unless asked)
```

Adapt names to client's domain. The structure is the principle, not the labels.

### Step 5: Design routing table

This is THE most valuable artifact. Format:

```
# Routing Rules
1. New strategy input → append to strategy.md
2. New client info → append to [client].md
3. New task → create in work/ with issue reference
4. Research output → reference/ (never root)
5. Meeting notes → active/ (or extract action items into work/)
6. Nothing fits → ASK. Do NOT create new file.
```

Rules must be:
- **Specific** (not "put it where it makes sense")
- **Exhaustive** (cover all common inputs)
- **Restrictive** (default = don't create new files)

**External input routing (critical rule):** Every interaction with the outside world – client calls, investor meetings, user interviews, support tickets – generates raw material. This material has a home:
1. Identify the canonical file for that source (client said it? → client file. User said it? → user research file.)
2. Append with timestamp and source attribution. Don't create a new file for each conversation.
3. If no canonical file exists for that source type → add a routing rule first, then append.

Unrouted external input is the #1 cause of file sprawl.

**Task file tracking rule:** Volatile-layer files (work/, tasks/) must link to a tracking reference – issue number, ticket ID, calendar event, or project milestone. No reference = no file. This prevents orphan task files that accumulate and rot. If the client doesn't use a tracker, the reference can be a date + one-line purpose, but it MUST exist.

**Structured data routing:** If the client has scripts or APIs that produce data files (JSON, CSV, database exports), add a routing rule: `Structured data from [source] → data/ or reference/ with collector script path noted. One file per data source. No manual edits – only the collector script updates it.` Pattern: one collector, one file, many consumer agents.

### Step 6: Design entry point

Choose based on client's tools:

| Tool | Entry point | Notes |
|------|------------|-------|
| Claude Code | CLAUDE.md | Thin wrapper → points to AGENTS.md if multi-tool |
| Cursor | .cursor/rules/ or .cursorrules | Thin wrapper → points to AGENTS.md |
| Codex / Copilot / Windsurf | AGENTS.md | Native support, Linux Foundation standard |
| Cowork | .auto-memory/MEMORY.md | Auto-loaded, add entry point instruction at top |
| Multiple tools | AGENTS.md (canonical) + thin wrappers for each | Single source of truth |

**Thin wrapper pattern** (when client uses multiple tools): AGENTS.md holds ALL canonical content. Each tool gets a thin wrapper (CLAUDE.md, .cursor/rules) that says "read AGENTS.md" + tool-specific rules only. Zero duplication between wrappers. Claude Code does NOT read AGENTS.md natively – it reads CLAUDE.md – so the thin wrapper bridges this gap.

Entry point content (keep SHORT – target <150 lines):
1. "Read [this file] first for any task related to [domain]"
2. Routing table (or pointer to it)
3. Critical rules (what's forbidden)
4. Source of truth declarations (which file is canonical for which topic)

**Why short:** Agent compliance drops sharply with entry point length. Field data: CLAUDE.md reduced from 800→150 lines = higher compliance. Independently confirmed: 847→127 lines, same result. Fewer rules → higher compliance. This is non-linear – a 200-line file is not "a little worse" than 150, it's meaningfully worse.

## Phase 3: Implementation

### Step 7: Create entry point file(s)

Start with AGENTS.md or CLAUDE.md. Content:
- File registry (what exists, where, what it's for)
- Routing table
- Boundary model (three tiers – see below)
- Nothing else. Short > long.

**Three-tier boundary model** (include in every entry point):
```
## Boundaries
CAN do autonomously: [list actions agent can take without asking]
MUST CONFIRM before doing: [list actions that need human approval]
FORBIDDEN: [list things agent must never do]
```
This is the most effective anti-mistake pattern. Three rows. Agents follow explicit boundaries more reliably than paragraph-form rules. Keep each tier to 3-5 items max.

**Target: <150 lines.** If the entry point exceeds 150 lines, you're putting content in it that belongs in referenced files. The entry point is a map, not an encyclopedia. What works: canonical paths, boundaries (can/must-confirm/forbidden), source of truth declarations, safe defaults. What doesn't work: abstract principles ("write clean code"), walls of text, duplicating rules across sections.

### Step 8: Move files to lifecycle-appropriate folders

- **Move, don't copy.** Copies = future divergence. Two copies of the same file WILL contradict each other within a month.
- Update ALL cross-references after moving. A moved file with stale references is worse than an unmoved file – now you have a ghost.
- Archive dead files (don't delete – client may need history).
- **Raw data files:** don't just move them – extract decisions/constraints/facts first, route extracted content per the routing table, THEN archive the raw source. Moving a raw transcript to reference/ doesn't make it useful; extracting the 3 key decisions from it does.
- After all moves: run a full cross-reference check. Every `[filename]` or path reference in every active file must resolve to an existing file. Zero ghosts is the target.

### Step 9: Eliminate duplicates

For each duplicate pair:
- Pick canonical source (usually the more maintained one)
- Replace the other with a pointer: "See [canonical-file.md] §section"
- If both have unique content, merge into canonical source

### Step 10: Set up file creation controls

Add to entry point:
```
## File Creation Rules
- NEVER create new files without [owner] approval
- Route new content to existing files per routing table
- If nothing fits → ASK, don't create
```

Also add to entry point – timeline convention for knowledge files:
```
## Timeline Convention
- New data goes ABOVE the last --- divider (top overrides bottom)
- Strategy decisions: update in place with timestamp, don't scatter same decision across sections
- Data and events: append with timestamp and source attribution
- Never delete old sections – agents need the timeline to understand why things changed
```

State the convention direction explicitly. Either direction works (top-overrides-bottom or bottom-overrides-top), but it MUST be declared. Ambiguity here = guaranteed agent confusion.

## Phase 4: Verification

### Step 11: Run "new agent" test

Start a fresh AI session (no conversation history). Run three task types:

**Task A – Knowledge question:** Ask a strategy or domain question that requires reading canon. Example: "What's our current pricing strategy?" Agent should find and cite the canonical file.

**Task B – Navigation:** Ask "where is [specific information]?" Agent should use the file registry or routing table to navigate, not grep blindly.

**Task C – Write with routing:** Ask the agent to add new information (a fake meeting note or decision). Agent should follow the routing table – append to the correct existing file, not create a new one.

Observe across all three:
- Does it find the entry point without hints?
- Does it read and follow the routing table?
- Does it navigate to the right files?
- Does it try to create unnecessary files?
- Is the output grounded in actual file content, not hallucinated?

### Step 12: Measure

- Root token count (target: <20K)
- Entry point line count (target: <150 lines)
- File count in root (target: <10)
- "New agent" test: 3/3 tasks completed without hints (target: at least 2/3)
- Zero orphan files outside archive/
- Zero ghost references

### Step 13: Hand off maintenance

Two maintenance mechanisms, both required:

**Reactive (every /improve pass):** Install `/improve` skill (see `improve/SKILL.md` in this folder). Part 2 handles reconciliation – keeping individual files current after each quality improvement pass.

**Proactive (quarterly):** Install `/context-architecture-cleanup` skill (see `context-architecture-cleanup/SKILL.md` in this folder). It audits the architecture itself: token count drift, orphan files, routing compliance, "new agent" test. Run quarterly, or when agent quality noticeably drops.

Without quarterly cleanup, any architecture degrades within 3-6 months. New files appear, routing gets ignored, token count drifts. The cleanup skill catches this before it becomes a full re-setup.

## What This Skill Does NOT Do

- Does not write the actual business content (strategy, product specs, etc.)
- Does not design AI agent prompts or workflows (that's a separate engagement)
- Does not handle model selection or API setup
- Does not create client-facing documents or reports
- Does not handle ongoing maintenance – that's `context-architecture-cleanup/SKILL.md` (quarterly) and `/improve` Part 2 (per-pass)

## Integration with Other Skills

After initial setup, two skills maintain the architecture:

**`/improve` (reactive, per-pass):** 
- Use it on any important artifact: strategy, spec, PRD, report, or other high-stakes output.
- Part 1 uses the context architecture to find source files
- Part 2 feeds findings back into files PER THE ROUTING TABLE
- Context lean check prevents bloat during reconciliation
- See `improve/SKILL.md` for the adapted version with context architecture rules

**`/context-architecture-cleanup` (proactive, quarterly):**
- Audits the architecture itself, not individual file content
- Automated checklist: token count, orphans, routing compliance, new agent test
- Outputs a cleanup report with proposed actions
- See `context-architecture-cleanup/SKILL.md` for the full procedure
