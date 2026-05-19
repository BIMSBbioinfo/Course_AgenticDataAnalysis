---
description: Triage new entries from Prompts/Logs/PROMPT_LOG.md into Prompts/implementation.md (Todo / In progress / Done)
argument-hint: [optional: since-date YYYY-MM-DD or "last"]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash(date:*), Bash(grep:*), Bash(wc:*), Bash(tail:*)]
---

# Triage Prompt Log into Implementation Backlog

You move *real* requests out of the auto-recorded `Prompts/Logs/PROMPT_LOG.md` and into the curated backlog in `Prompts/implementation.md`. This is the bridge between raw conversation and tracked work.

---

## Phase 1: Locate and read the log

1. Verify `Prompts/Logs/PROMPT_LOG.md` exists. If not, tell the user "no prompt log found — the auto-capture hook only writes inside research-setup projects" and stop.
2. Verify `Prompts/implementation.md` exists. If not, create it with the three section headers `## Todo`, `## In progress`, `## Done` plus a one-line preface.
3. Determine the cutoff:
   - If `$ARGUMENTS` is `last`: find the most recent timestamp already referenced in `implementation.md` (look for a `[log: <iso>]` marker on any item) and use that as the lower bound.
   - If `$ARGUMENTS` is a date (`YYYY-MM-DD`): use it.
   - Otherwise: ask the user "triage entries since when? (latest tracked / today / a date)".
4. Read entries in `PROMPT_LOG.md` newer than the cutoff.

---

## Phase 2: Classify each entry

For each prompt entry, decide one of:

| Bucket | What it looks like |
|--------|-------------------|
| **Real request** | A new task, idea, refactor, analysis, or instruction — anything that *should* leave a trace. |
| **Continuation / clarification** | "no actually", "wait", "yes do that", typos, conversational corrections of an in-progress task. Merge with the parent request rather than creating a new item. |
| **Question / exploration** | "what does X do?", "where is Y?". Skip — these don't need backlog tracking. |
| **Already tracked** | Matches an existing `## Todo` / `## In progress` / `## Done` item. Skip. |
| **Hot-fix** | Trivial cosmetic ask ("fix the axis label", "rename column"). Skip backlog; the prompt log already preserves provenance. |

Do not be aggressive about promoting — implementation.md is for things that warrant a canvas. When in doubt, ask the user.

---

## Phase 3: Propose the new Todo items

Show the user a numbered list of proposed Todo items, each as:

    - [ ] <one-line summary> [log: <iso>] [session: <8char>]
      Source: "<first ~80 chars of the prompt verbatim>"

Ask for approval. Accept feedback like "merge 2 and 3", "drop 4", "rename 1 to ...".

---

## Phase 4: Write to implementation.md

1. Append approved items under `## Todo` in `implementation.md`, preserving any existing items.
2. Do **not** modify `PROMPT_LOG.md` — it stays append-only.
3. Show the user a final summary: `N entries reviewed, M promoted to Todo, K skipped`.

---

## Phase 5: Suggest next step

Recommend `/plan-convert <item>` for the most actionable Todo item, with a one-line justification (it's a quick win / it unblocks others / the user just asked for it).
