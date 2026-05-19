---
description: Turn an item from Prompts/implementation.md into a structured canvas at Prompts/canvases/NNN_slug.md
argument-hint: [next | item-number | item-text]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(date:*), Bash(mkdir:*), Bash(git status:*), Agent]
---

# Convert Implementation Item to Structured Canvas

You take a single item from `Prompts/implementation.md` and turn it into a structured canvas file at `Prompts/canvases/NNN_slug.md`. The canvas captures *intent* in a form that survives separately from the code that comes from it.

---

## Phase 1: Pick the item

1. Read `Prompts/implementation.md`. If missing, tell the user the file isn't there and stop.
2. Resolve `$ARGUMENTS`:
   - `next` (literal token): take the **first** item from `## Todo` (item #1). If `## Todo` is empty, tell the user and stop.
   - A **number** (e.g. `2`): take the Nth item from `## Todo`.
   - **Text**: fuzzy-match against Todo items.
   - **Empty**: list all Todo items and ask the user which one.
3. Read the source-prompt log entry referenced by the item (the `[log: <iso>]` marker) so you have the user's verbatim wording for context. If the item has no `[log:]` marker (e.g. it came from `/research-to-implementation` and carries `[phase: N]` instead), skip this step and use the item's own text as the wording.

---

## Phase 2: Allocate the canvas number and slug

1. List `Prompts/canvases/`. Find the highest existing `NNN_*.md`. New canvas is `NNN+1` zero-padded to 3 digits.
2. Generate a kebab-case slug from the item summary (max 5 words, lowercase, hyphens). Examples: `qc-pca`, `normalization`, `pirna-deseq2`.
3. Final filename: `Prompts/canvases/NNN_slug.md`.

---

## Phase 3: Gather context before writing

Launch a small Explore agent (or do it yourself if scope is tiny) to scan:
- What data is available in `Data/` and `Documentation/` relevant to this task?
- What upstream reports/canvases produce inputs this task needs?
- What downstream reports/canvases would consume this task's outputs?
- What helper functions in `Scripts/Bin/` are reusable?
- Any prior `dependencies.json` nodes worth wiring to.

---

## Phase 4: Draft the canvas

Write the file using this exact structure:

    ---
    id: NNN
    slug: <slug>
    created: <YYYY-MM-DD>
    source_prompt_log: <iso timestamp from PROMPT_LOG.md>
    implementation_md_item: "<verbatim Todo line summary>"
    status: todo
    ---

    # Question

    <One sentence stating the scientific or technical question this answers.>

    # Entities

    <Bullet list of data tables, samples, features, metadata involved. Reference exact paths (Data/..., cacheR ids).>

    # Approach

    <Methods, packages, parameters, statistical tests, normalization, thresholds. Be specific. Cite a paper or tool when relevant.>

    # Structure

    - **Upstream**: <list of canvases / reports / data this depends on>
    - **Downstream**: <list of canvases / reports / outputs this enables>
    - **Lives in**: `Scripts/Reports/NN_<name>.Rmd` (and helpers in `Scripts/Bin/<file>.R`)

    # Operations

    1. <Numbered step>
    2. <...>

    # Safeguards

    - <Sanity check or oracle test>
    - <Validation against an established tool when applicable>
    - <What "done" looks like — concrete, observable>

**Rules:**
- Do not invent parameters. Where the user hasn't specified (e.g. p-value cutoff), write `TBD — confirm with user` rather than guessing.
- The Approach section is the single most important; spend the most thought there.
- Keep Operations to 5–10 numbered steps. If more, the canvas is too big — split into two.

---

## Phase 5: Update implementation.md

1. Move the source item from `## Todo` to `## In progress` and append a backlink: `→ Prompts/canvases/NNN_slug.md`.
2. Do not delete or reorder other items.

---

## Phase 6: Confirm and suggest next step

1. Show the user the new canvas path.
2. If any sections were marked `TBD`, list them so the user can fill in before generation.
3. Recommend next: review the canvas, then run `/plan-exec` or write the implementation, then commit with trailer `Implements: Prompts/canvases/NNN_slug.md`.

Do **not** generate the implementation code in this command — that's a separate step. The whole point is to lock down the *prompt* before the *code*.
