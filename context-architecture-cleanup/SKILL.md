---
name: context-architecture-cleanup
description: |
  Quarterly maintenance audit for an existing context architecture. Checks for entropy: token count drift, orphan files, routing violations, stale content, broken cross-references, and "new agent" test regression. Outputs a cleanup report with proposed actions. Use when: architecture was set up (by context-architecture-setup or manually) and needs maintenance, agent quality has degraded over time, token count has grown, user suspects file sprawl, user wants a quarterly health check, user says "clean up context", "audit my files", "context is getting messy again", "run cleanup". Also use after major project milestones (launch, pivot, fundraise close) when context shifts significantly. This skill assumes an architecture already EXISTS – if no entry point or routing table exists, use context-architecture-setup first.
---

# Context Architecture Cleanup

> **Prerequisite:** A context architecture must already exist (entry point file + routing table + lifecycle-split folders). If none exists, use `context-architecture-setup/SKILL.md` first.
> **Reference:** `Context Architecture.md` (same parent folder) for principles and theory.
> **Frequency:** Run quarterly, or when agent quality noticeably drops, or after major project milestones.

## What This Skill Does

Audits an existing context architecture for entropy and drift. Produces a cleanup report and executes approved fixes. Think of it as a health check: setup builds the system, cleanup keeps it working.

**Setup vs Cleanup:**
- **Setup** (context-architecture-setup): from scratch or from mess → structured architecture. ~6 hours, one-time.
- **Cleanup** (this skill): from structured architecture that drifted → re-verified architecture. ~2-3 hours, repeatable.

---

## Phase 1: Measure Current State

### Step 1: Read entry point and routing table

Read the entry point file (AGENTS.md, CLAUDE.md, or equivalent). Extract:
- File registry (what files should exist)
- Routing table (what goes where)
- Critical rules (what's forbidden)
- Any declared conventions (timeline direction, file creation rules)

If no entry point exists → stop. Recommend `context-architecture-setup` instead.

### Step 2: Count tokens

Count total tokens across all active .md files (exclude archive/deprecated).

Compare against baseline:
- If baseline exists (from previous cleanup or initial setup) → calculate drift %
- If no baseline → this count becomes the baseline

**Thresholds:**
- Stable or decreased → healthy
- +10-25% → minor drift, investigate
- +25%+ → significant bloat, prioritize cleanup

### Step 3: Inventory all files

List every file the agent would read on startup or during tasks. For each file, record:
- Path
- Size (bytes/tokens)
- Last modified date
- Lifecycle layer (canon/reference/active/volatile/archive)
- Referenced in entry point? (yes/no)

---

## Phase 2: Run Diagnostic Checks

### Check 1: Orphan files
Files with zero inbound references from entry point or other active files.
- **Expected:** zero outside archive/deprecated
- **Action:** for each orphan – should it be in the registry? Or deprecated?

### Check 2: Ghost references
References in entry point or active files that point to files that don't exist.
- **Expected:** zero
- **Action:** update or remove each dead reference

### Check 3: Routing compliance
Were any new files created since last cleanup? Check:
- Does the routing table have a rule covering this file?
- Was it created per the file creation rules?
- Could its content have been appended to an existing file instead?
- **Action:** for non-compliant files – merge into canonical file or add routing rule

### Check 4: Duplicate content
Same topic described in multiple files.
- Scan for overlapping content (same names, dates, decisions in 2+ files)
- **Expected:** zero duplicates outside archive
- **Action:** pick canonical source, replace other with pointer

### Check 5: Stale content
Files or sections that haven't been updated but describe things that change:
- Active-layer files not modified in 30+ days → may be stale or should move to reference/archive
- Volatile-layer files older than 7 days → should be archived or deleted
- **Action:** verify currency, archive or update

### Check 6: Lifecycle misplacement
Files in wrong lifecycle folder:
- Canon files that change weekly → should be in active
- Volatile files that haven't changed in months → should be in archive
- **Action:** move to correct layer, update references

### Check 7: Entry point health
- Is the entry point under 150 lines? (Short > long for agent compliance)
- Does the routing table cover all common inputs?
- Are source-of-truth declarations current?
- Does it reference all active files?
- **Action:** trim, update, fill gaps

---

## Phase 3: "New Agent" Test

Start a fresh AI session with no conversation history. Give it a real task from the workspace domain.

Observe and score (pass/fail):
1. Agent finds the entry point without hints
2. Agent reads the routing table
3. Agent navigates to the correct source file for the task
4. Agent does NOT create unnecessary new files
5. Agent output is grounded in actual file content, not hallucinated

**Target:** 4/5 pass minimum. Below 4 → entry points or routing need work.

Compare against baseline (from setup or previous cleanup):
- Same or better → architecture is holding
- Worse → investigate what changed since last cleanup

---

## Phase 4: Cleanup Report

Present findings as a structured report:

```
## Context Architecture Cleanup Report
Date: YYYY-MM-DD
Baseline token count: [from last cleanup or setup]
Current token count: [measured]
Drift: [+/- %]

### Findings
| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | Orphan files | ✅/⚠️/❌ | [count and list] |
| 2 | Ghost references | ✅/⚠️/❌ | [count and list] |
| 3 | Routing compliance | ✅/⚠️/❌ | [violations] |
| 4 | Duplicate content | ✅/⚠️/❌ | [pairs] |
| 5 | Stale content | ✅/⚠️/❌ | [files] |
| 6 | Lifecycle misplacement | ✅/⚠️/❌ | [files] |
| 7 | Entry point health | ✅/⚠️/❌ | [issues] |
| 8 | New agent test | [score]/5 | [observations] |

### Proposed Actions (ranked by impact)
1. [action] – fixes check [#], saves [X] tokens
2. [action] – fixes check [#], removes [Y] orphans
...

### Health Score: [X/8 checks passing]
```

---

## Phase 5: Execute Approved Fixes

For each approved action:
1. Read the target file from disk before editing
2. Apply the fix (move, merge, deprecate, update reference, trim)
3. Update entry point if any file paths changed
4. Verify no new orphans or ghosts created by the fix

After all fixes:
- Re-count tokens → record as new baseline
- Update entry point with cleanup timestamp
- Run one final cross-reference check

---

## What This Skill Does NOT Do

- Does not create an architecture from scratch – use `context-architecture-setup` for that
- Does not improve individual file content – use `/improve` for that
- Does not write business content (strategy, specs, etc.)
- Does not handle model selection or AI tool configuration
