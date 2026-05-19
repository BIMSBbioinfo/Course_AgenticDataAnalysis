---
description: Execute uncompleted items from an implementation plan, then commit all changes. Optionally pass a plan file path and/or task numbers (e.g. /plan-exec, /plan-exec 3, /plan-exec Prompts/my_plan.md, /plan-exec Prompts/my_plan.md 1,3,5).
argument-hint: [plan-file] [task-number(s) | all | next]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Agent]
---

# Implementation Plan Execution

You are executing uncompleted items from an implementation plan. Follow each phase sequentially.

---

## Phase 1: Locate and Parse the Plan

**Actions**:
1. Parse `$ARGUMENTS` into whitespace-separated tokens. The first token is a **plan-file** if it (a) ends in `.md`, (b) contains `/`, or (c) matches an existing file on disk. Otherwise treat all tokens as task selectors.
2. Determine the plan file:
   - If a plan-file token was provided: use it (resolve relative to the working directory; error out if missing)
   - Else, apply this precedence:
     1. `Prompts/implementation.md` (new prompt-driven pipeline)
     2. `Prompts/implementation_plan.md` (legacy)
     3. `Glob **/implementation.md` then `**/implementation_plan.md`
   - If both `implementation.md` and `implementation_plan.md` exist in the same project, prefer the new one and warn.
3. Read the full plan file. Note the format:
   - **New format** = `## Todo` / `## In progress` / `## Done` sections, items shaped `- [ ] <text> [log: ...] [session: ...]` optionally with `→ Prompts/canvases/NNN_slug.md` backlinks.
   - **Legacy format** = free-form checkbox items.
4. If not found, inform the user and stop
5. Also read `Prompts/CHANGELOG.md` if it exists
6. Extract uncompleted items, numbering sequentially:
   - **New format**: items under `## Todo` AND `## In progress` (both are "not yet done"). Canvas-linked `In progress` items take priority — they're already structured and ready to execute.
   - **Legacy format**: lines with `[ ]` or unmarked items under TODO sections.
7. Determine which items to execute from the remaining (non-plan-file) tokens:
   - If `next`: execute only the **first** uncompleted task (task #1 in the numbered list)
   - If a **number** is provided (e.g., `3`): execute only that specific task item
   - If **multiple numbers** are provided (e.g., `1,3,5` or `1 3 5`): execute those specific items
   - If `all` or **no task token**: present the numbered list to the user and ask which items to execute (or confirm "all")

**Examples of argument parsing**:
- `/plan-exec` → default plan file, ask user
- `/plan-exec next` → default plan file, first uncompleted task
- `/plan-exec 3` → default plan file, task 3
- `/plan-exec all` → default plan file, all tasks
- `/plan-exec Prompts/my_plan.md` → `Prompts/my_plan.md`, ask user
- `/plan-exec Prompts/my_plan.md next` → `Prompts/my_plan.md`, first uncompleted task
- `/plan-exec Prompts/my_plan.md 3` → `Prompts/my_plan.md`, task 3
- `/plan-exec Prompts/my_plan.md 1,3,5` → `Prompts/my_plan.md`, tasks 1, 3, and 5
- `/plan-exec Prompts/my_plan.md all` → `Prompts/my_plan.md`, all tasks

---

## Phase 1b: Pre-flight — Commit Pending Plan Edits

**Goal**: Keep manual plan edits separate from implementation commits

**Actions**:
1. Skip this phase if the working directory is not a git repo
2. Run `git status --porcelain -- <plan-file>` (and `Prompts/CHANGELOG.md` if it exists)
3. If either file has staged or unstaged changes:
   - Stage only those files (do NOT use `git add -A`)
   - Commit with message: `docs: refine plan`
   - Show the commit hash to the user so they know it happened
4. Proceed to Phase 2 with a clean plan-file state

This ensures the upcoming implementation commit only contains code changes, not the user's manual plan edits.

---

## Phase 2: Execute Each Item

**Goal**: Implement each selected TODO item from the plan

**Actions**: for each selected item:

1. **Check for a canvas backlink** on the item line — look for `→ Prompts/canvases/NNN_slug.md`.

2. **If a canvas exists**:
   a. Read the canvas file. Validate it has the standard sections (Question / Entities / Approach / Structure / Operations / Safeguards).
   b. For each canvas listed under `# Structure → Upstream`, read that canvas's `# Operations` and `# Safeguards` so dependencies are loaded into context.
   c. If any `# Operations` step contains the literal token `TBD`, **STOP** and tell the user: "Canvas NNN has unresolved TBD items in Operations — edit `Prompts/canvases/NNN_slug.md` and fill them in before re-running. Honoring fix-the-prompt-first." Move to the next item.
   d. Use the canvas's `# Operations` as the **step list — do not invent extra steps**. Each numbered Operation is a unit of work.
   e. Use the canvas's `# Safeguards` as the **done-criteria**. The last bullet is typically `Done = ...`; that line is the acceptance test.
   f. Read any files referenced in `# Entities` (data paths, helper files) to ground the implementation.

3. **If no canvas linked** (Todo item without backlink, or legacy plan format):
   - Read any referenced files (reports, scripts, data files) to understand current state
   - Identify what code changes are needed from the item's text alone
   - Make reasonable choices based on project context

4. **Implement the changes**:
   - Edit existing `.Rmd` reports, `.R` scripts, or other files as specified
   - Follow existing code conventions found in the project
   - Test changes where possible (R syntax, paths exist)

5. **Mark the item done**:
   - **New format**: move the item from its current section (`## Todo` or `## In progress`) to `## Done` in `implementation.md`. If a canvas is linked, also update the canvas YAML `status: done` — keep them in lockstep.
   - **Legacy format**: change `[ ]` to `[x]` in `implementation_plan.md`.

6. **Keep a running log per item** noting what was changed (used by Phases 3-5).

**Guidelines**:
- Work through items sequentially unless independent items can be parallelized
- If an item requires data that doesn't exist, skip it and note the blocker
- If an item is ambiguous AND has a canvas, re-read the canvas's Question + Approach; if still ambiguous, ask the user (fix-the-prompt-first)
- Do NOT render reports unless explicitly requested — just edit the source files
- Prefer minimal, targeted edits over large rewrites

---

## Phase 3: Update the Changelog

**Goal**: Document what was implemented

**Actions**:
1. Read the existing `Prompts/CHANGELOG.md` (create `Prompts/` directory if needed)
2. Add a new version entry at the top with today's date
3. List all items that were completed with brief descriptions. **For canvas-linked items**, append the canvas reference:
   ```
   - NNN <slug> — <one-line outcome> [canvas: Prompts/canvases/NNN_slug.md]
   ```
   Items without a canvas keep the previous free-form format.
4. Note any items that were skipped and why (including TBD-halted canvases — these are not failures, they need user input).

---

## Phase 4: Commit All Changes

**Goal**: Create a single commit with all implementation work

**Actions**:
1. Run `git status` to see all changed files
2. Run `git diff` to review changes
3. Stage all relevant files (reports, scripts, plan, changelog, canvases that were status-bumped — NOT data files or large binaries)
4. Create a descriptive commit message summarizing what was implemented. **For each canvas-linked item, add an `Implements:` trailer at the end of the message body** (multiple trailers are fine):
   ```
   feat: implement plan items - [brief list of what was done]

   - Item 1 description
   - Item 2 description
   ...

   Implements: Prompts/canvases/NNN_slug.md
   Implements: Prompts/canvases/MMM_other_slug.md
   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```
   Items without a canvas don't get an `Implements:` trailer. Use `git interpret-trailers` if you want to verify trailers are well-formed before committing.
5. Confirm the commit to the user and show `git log --oneline -1`

---

## Phase 5: Summary

**Goal**: Report back to the user

**Actions**:
1. List all completed items with key changes made. **For canvas-linked items, report against each canvas's `# Safeguards`**:
   - State whether each safeguard was satisfied (✓ / ✗ / partial)
   - Quote the canvas's "Done = ..." line and say explicitly whether the condition is met
   - If any safeguard was missed, surface it — this is the actionable signal, not a footnote
2. List any skipped items with reasons (TBD-halted canvases especially).
3. Show the commit hash and message.
4. Suggest what to work on next based on remaining uncompleted items. If `In progress` items remain with canvases, prefer those over fresh `Todo` items.

---
