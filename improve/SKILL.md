---
name: improve
description: |
  Iterative quality improvement for any AI output — getting to 9.999/10 through structured critique, re-reading source files, deep research, and rewriting. Use this skill when: the user asks to review, critique, or improve any output; the user says the output is weak, shallow, or "scratching the surface"; the user asks to re-read context and find what was missed; the user wants MECE coverage; the user asks for "non-obvious connections" or a "third perspective"; the user signals high stakes ("you have one chance", "don't miss anything", threats to replace with another agent); the user asks to "think harder" or "go deeper". Also trigger for critique of the user's own documents, strategies, or plans. This skill is about extracting the absolute maximum quality through systematic iteration — not settling for "good enough." After delivering improved output, this skill also reconciles source .md files against audit findings — proposing edits the user must explicitly approve or reject before moving on.
---

# Improve: Getting to 9.999/10

Everything in this skill is always-on. Every technique, every pass.

This skill has two parts:
- **Part 1** — Iterative quality improvement of the output itself (Steps 0–10 + quality lenses)
- **Part 2** — Source material reconciliation: feeding audit findings back into .md context files so they stay accurate for future use (Steps 11–14)

Both parts are mandatory. Part 2 begins after the user accepts the improved output.

---

## CONTEXT ARCHITECTURE RULES (read first)

> These rules govern how this skill interacts with the file system. They prevent context bloat and maintain the architecture set up by `context-architecture-setup`.

1. **NEVER create new .md files during reconciliation.** Route all findings to existing files per the routing table (in CLAUDE.md, AGENTS.md, or equivalent entry point). If no existing file fits → propose adding a routing rule, not a new file.
2. **Read the routing table before proposing any edit.** If the workspace has CLAUDE.md or AGENTS.md with routing rules, follow them. The routing table determines WHERE edits go. **If no routing table exists:** ask the user which file each finding belongs in. Do not guess – unrouted edits create sprawl.
3. **Strategy decisions: update in place with timestamp.** Don't create new sections that duplicate old ones. Find the original section, update it, add `(updated YYYY-MM-DD)`. Keep the previous version as a one-line note if versioning matters.
4. **Data and events: append with timestamp, following the file's stated convention.** If the file says "top overrides bottom" – add new data ABOVE the last `---`. If "bottom overrides top" – add BELOW. If no convention is stated – check the entry point (CLAUDE.md / AGENTS.md) for the default. Don't rewrite old sections for events/facts – they're history.
5. **Before proposing edits, ask: does this make context leaner or fatter?** Lean is always better. Every new section, every new cross-reference = maintenance cost. If an edit adds complexity without proportional value — don't propose it.
6. **Cross-references: use paths relative to a stated root.** Don't use ambiguous relative paths. If the workspace has a declared root convention, follow it.
7. **After reconciliation: check for orphans.** Did your edits create any dead references? Did any file lose its last inbound link? Clean up.
8. **This file is an architecture-focused variant.** It is adapted for context architecture workflows and may differ from other local copies of `/improve`.

---

## PART 1: OUTPUT IMPROVEMENT

## Step 0: Decide whether to refine at all

Check if the output actually needs refinement. Uniformly refining all outputs degrades overall quality — good outputs get over-corrected into worse ones.

Re-read the output against the task requirements. If it already addresses every requirement with specifics from the source files, and you can't identify a concrete flaw — stop. Return as-is.

If you identify concrete flaws — proceed.

## Step 1: Re-read source files from disk

Context compaction corrupts your model of what the files say. Use the Read tool on every relevant source file before critiquing. The user's files are ground truth. Your memory of them is lossy compression.

## Step 2: Extract task requirements as a checklist

Go back to the user's original request. Write down every explicit and implicit requirement as a checklist. Each item becomes a scoring dimension. The output is evaluated against THIS CHECKLIST — not against your sense of "seems fine."

## Step 3: Snapshot the current version

Before any edits, take a mental snapshot: every fact, number, name, structural element, and key phrase in the current output. This is your rollback target. If anything from this snapshot disappears or degrades after editing — revert that specific section and re-attempt.

## Step 4: Critique — separate the critic from the generator

Do NOT self-critique in your own voice. You systematically overrate what you just wrote. Self-bias amplifies with each pass.

Instead, adopt a separate critic role. You are now an adversarial reviewer who did NOT write this output. Your job is to find what's wrong, what's missing, what's shallow. Ask for each element:

- Does it address the task requirement it claims to address? (validate against checklist)
- Is it as specific and deep as the source files allow? (validate against sources)
- What would the user's toughest critic say about this? (adversarial simulation)
- What would falsify this claim?

Present critique to the user as:
- **Strong** — passed all checks against task + sources. Lower priority this pass, but NOT exempt from future questioning
- **Weak** — failed at least one check
- **Missing** — task requirement not addressed
- **Wrong** — factual errors or stale data

## Step 5: Ask the user to score key dimensions (1–5)

Invite the user to rate 2–3 dimensions that matter most (1–5 scale). Their scores override your internal rubric. A dimension you rated 4/5 that the user rates 2/5 is your #1 blind spot.

If the user declines to score — proceed, but flag internally that the output has no external validation.

## Step 6: Research gaps before rewriting

When critique reveals knowledge gaps, research BEFORE rewriting. Don't fill gaps with plausible generalities.

- Use current year in search queries
- Prefer named practitioners and papers over generic guides
- Three independent sources = signal; one blog post = opinion
- Tag confidence: well-established / emerging / speculative / single-source

## Step 7: Apply surgical edits, not full rewrites

Full rewrites carry the highest regression risk. Edit only the sections identified as Weak, Missing, or Wrong. Do not touch Strong sections unless the user specifically asks.

## Step 8: Run regression checks

After editing, verify against the snapshot (Step 3):

- **Entity retention**: every name, number, date, specific claim — still present and accurate?
- **Structure preservation**: every section header, structural element — still in place?
- **No new unsupported claims**: did the edit introduce facts not in the source files?
- **No detail loss**: did any concrete detail get replaced by a vague summary?
- **No scope creep**: did anything get added that the user didn't ask for?

If ANY check fails — revert that section and re-attempt more narrowly.

Risk tiers (safest → most dangerous):
1. **Polishing** — low risk, watch for voice erosion and meaning drift
2. **Adding missing content** — moderate risk, watch for scope creep
3. **Factual correction** — high risk, watch for introducing new errors
4. **Structural reorganization** — HIGHEST risk. Avoid unless explicitly requested. If unavoidable, lock key facts and numbers before moving anything

## Step 9: Context hygiene between passes

After each pass, collapse the critique into a short summary of what changed and what's still open. Do not carry forward the full critique history into the next pass — it degrades performance and pollutes context.

## Step 10: Adaptive stop

Hard cap: 3 passes maximum. Quality gains plateau after 1–3 passes. After pass 3, self-bias makes further passes actively harmful.

Stop earlier if:
- No concrete flaws found in Step 0
- User scores all key dimensions 4+/5
- Quality delta between passes is negligible

After stopping: "I think this is near the ceiling without [specific thing needed — a user decision, new data, an expert opinion]."

---

## PART 2: SOURCE MATERIAL RECONCILIATION

Part 2 activates after the user accepts the improved output (or at any point when the user flags something wrong in the source materials). The goal: feed reality-checked findings back into the .md context files so future sessions start from truth, not stale assumptions.

This is not optional. Stale source files poison every future conversation. Part 2 is how the knowledge base stays alive.

## Step 11: Read routing table + audit source files

**First:** read the entry point file (CLAUDE.md / AGENTS.md) to get the routing table and file registry. You need to know WHERE edits should go before proposing them.

**Then:** re-read each source .md file used in Part 1. For each file, compile a list of discrepancies:

- **Stale** — information that was true when written but is no longer accurate
- **Missing** — insights or decisions that should be captured but aren't in any .md file
- **Contradictory** — two .md files say different things about the same topic
- **Vague** — a claim that the improve process forced you to make concrete

**Cross-file contradiction sweep:** After per-file audit, explicitly check for contradictions BETWEEN files. For each key claim (strategy decisions, numbers, priorities, timelines) found in one file — grep/search for the same topic in other files. If two files disagree, surface both with dates and file paths. The NEWER timestamp wins by default, but flag for user confirmation — the older claim might be intentionally preserved.

Procedure:
1. Extract key claims from the file you just audited (strategy, numbers, priorities)
2. For each claim, search other .md files for the same topic
3. If found — compare. Same? Skip. Different? Flag as contradiction with both timestamps
4. Present contradictions grouped: "File A (March 15) says X. File B (April 2) says Y. Which is current?"

If Part 1 found zero discrepancies and the user hasn't flagged anything — skip to Step 14 and confirm: "Source files look current, no edits needed."

## Step 12: Propose edits (routed by architecture)

For each proposed edit, determine the TARGET FILE using the routing table. Do NOT create new files.

Present each proposed edit clearly. Group by file. For each edit, include:

1. **File**: which .md file (per routing table)
2. **Section**: where in the file (quote a short anchor phrase)
3. **Current text**: what's there now (brief excerpt)
4. **Proposed change**: the new text, with a timestamp
5. **Why**: one sentence explaining the trigger
6. **Edit type**: append (new data) or update-in-place (strategy decision change)

Also trigger Step 12 whenever the user says something like:
- "That's wrong in the doc"
- "This is outdated"
- "We changed this"
- Any correction to a fact that originated from a .md file

In these cases, immediately propose the edit to the relevant .md file. Don't just acknowledge conversationally — capture the correction.

## Step 13: Persist until resolved

Every proposed edit needs an explicit user response: approved, rejected, or modified. Do not let unresolved proposals silently die in the conversation.

Rules:
- If the user responds to the improved output but ignores the edit proposals — resurface them.
- If the user addresses some proposals but not all — list the remaining ones.
- If the user changes topic — at the next natural pause, bring open edits back.
- Hard cap: resurface up to 3 times per conversation. After 3 attempts, note the unresolved items one final time and move on.
- If the user explicitly says "skip all" or "I'll handle it later" — accept that and stop.

The point is not to annoy — it's to prevent knowledge rot.

## Step 14: Apply approved edits + architecture check

For each approved edit:
1. Read the target .md file from disk (don't rely on cached content)
2. Apply the edit using str_replace or targeted insertion
3. For strategy decisions: update in place with `(updated YYYY-MM-DD)`
4. For data/events: append below last `---` with timestamp
5. Confirm to the user: "Updated [filename] — [brief description of change]"

**Post-edit architecture check:**
- Did any edit create a dead cross-reference?
- Did any edit duplicate information that exists elsewhere?
- Is the total file count the same as before? (should be — no new files)
- Did root token count increase? If so, is the increase justified?

---

## The quality lenses — all always on

Apply every one on every pass. Not sequential — simultaneous filters during critique and editing.

**1. MECE** — check every structural element for completeness and overlap.

**2. Falsification** — for every major claim, actively try to break it.

**3. Cross-context connection mining** — look for latent links between facts in different source files that the user hasn't connected.

**4. The "new agent" test** — would a fresh agent with zero conversation history understand this output without clarifying questions?

**5. Contradiction detection** — for every key claim in the output, verify it doesn't conflict with other .md files. Search by topic, not by file. When found: quote both sources with timestamps and file paths. Don't silently pick one — surface the conflict.

**6. Audience adversarial simulation** — simulate the reader's toughest pushback.

**7. Concrete over abstract** — replace every "various", "several", "significant" with the actual thing.

**8. Recency check** — prefer last-6-month sources. Tag dates on market/practice claims.

**9. Task drift detection** — after every pass, re-check the original task checklist. Did improvement drift from what the user asked?

**10. Context lean check** — does this edit make the context system leaner (fewer files, fewer cross-references, cleaner routing) or fatter? If fatter: is the added complexity proportional to the value? Default answer: keep it lean.
