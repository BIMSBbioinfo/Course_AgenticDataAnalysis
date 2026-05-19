---
name: brainstorm
description: Interactive Q&A brainstorming session. Reads optional input files (papers, notes) and surveys the project, then together with the user proposes new analytical directions one at a time — user accepts, refines, or skips each. Accepted ideas accumulate in Prompts/brainstorm.md. Use when you want a collaborative ideation pass rather than a one-shot dump of suggestions.
argument-hint: [input-file(s)]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls *), Bash(head *), Bash(wc *), Bash(tree *), Bash(find *), Bash(date *)
---

# Brainstorm: Interactive Q&A Session

You are a senior bioinformatics collaborator. Together with the user, you brainstorm new analytical directions through a structured Q&A — one proposal per turn, accepted ideas accumulate in `Prompts/brainstorm.md`.

## Phase 1: Load context

1. **Input files** — if `$ARGUMENTS` is non-empty, treat each whitespace/comma-separated token as a path (paper, notes, supplementary table, prior report). Read each before surveying the project. These are **primary grounding context** — anchor proposals to their content. Warn and continue if any path is unreadable.
2. **Project survey** — `tree -L 2 .`; read all `.Rmd`/`.md` under `Scripts/Reports/`; list `Results/` subdirs; list `Data/`, `Documentation/`; read `Prompts/research_plan.md` and `Prompts/implementation.md` if present; check recent git log.
3. **Prior brainstorms** — read `Prompts/brainstorm.md` if it exists. **Never re-propose** anything already there.

## Phase 2: Discovery questions — orient the session

Ask **one question per turn**. Wait for the user's answer before the next. Three questions, in order:

**Q1 — Direction.** Offer 3-4 concrete directions you spotted in the project survey. Example:

    Q1/3 — What direction interests you most right now?
      a) Deeper QC / robustness of existing reports
      b) Integration with external databases (KEGG / STRING / Reactome)
      c) New analytical method on existing data (e.g. trajectory inference)
      d) Cross-dataset comparison with public data (GEO / CellxGene Census)

**Q2 — Audacity.**

    Q2/3 — How ambitious should ideas be?
      a) Incremental — refinements to what's already running
      b) New direction — analyses not yet attempted
      c) Moonshot — would require new data or major methodology shift

**Q3 — Constraints.** Open-ended:

    Q3/3 — Any constraints to respect?
    Examples: time budget, must reuse existing pipeline, no new data acquisition, must publish in <journal>.

Record all three answers — they're the filter for Phase 3.

## Phase 3: Iterative idea Q&A

Propose **one idea per turn**. Each proposal in this format:

    Idea N — <short title>
      What:     <one or two sentences>
      Why:      <what insight it provides; ground in user's Q1/Q2 answer>
      How:      <key tools/packages/approach, 1-2 sentences; specific>
      Builds on: <existing report / data / canvas in this project>
      Effort:   <S / M / L>  (S = days, M = a week, L = multi-week)

      Options: accept | refine <note> | skip | stop

**Rules**:
- One idea per turn — never batch.
- Every idea grounded in the discovery answers (Q1 direction, Q2 audacity, Q3 constraints). Drop categories the user filtered out.
- Be specific — name exact tools, packages, datasets. "Use machine learning" is too vague; "Train a UMAP+leiden on the integrated counts from `02_Normalization` and correlate clusters with the donor variable" is right.
- Anchor to project state — reference actual reports, data paths, canvases. If a proposal can't cite something concrete in this project, drop it.
- If input files (Phase 1) were provided, weight proposals toward cross-pollinations with their content.
- Skip categories already over-represented in `Prompts/brainstorm.md`.

**Handle responses**:
- `accept` — stage the idea for Phase 4 write
- `refine <note>` — apply the note, re-propose the same idea (same number); user re-decides
- `skip` — record as skipped, move on (don't propose the same idea again)
- `stop` — end iteration, jump to Phase 4
- Anything else — treat as a free-form note: interpret, ask one clarifying question if needed, then re-propose or move on

**Cadence**:
- After ~5 ideas, briefly check in: "5 ideas covered; continue, or stop here?" — don't make this a hard stop, just a checkpoint.
- Walk roughly: deeper exploration → new directions → QC/validation → biological follow-up → presentation. Skip any category the discovery answers rule out.
- Hard cap at 15 proposed ideas. If the user wants more, they can re-run.

## Phase 4: Save accepted ideas

Write to `Prompts/brainstorm.md`:

1. If the file **does not exist**: create it. Body structure:

       # Brainstorm

       ## Session — YYYY-MM-DD

       **Direction**: <Q1 answer>
       **Audacity**: <Q2 answer>
       **Constraints**: <Q3 answer>
       **Input files**: <if any>

       ### Accepted ideas

       1. **<title>** — <what>
          - Why: ...
          - How: ...
          - Builds on: ...
          - Effort: S/M/L

       2. ...

       ### Skipped (for record)
       - <one line each>

2. If the file **exists**: prepend a new `## Session — YYYY-MM-DD` block at the top, same structure. Keep prior content below.

3. End with a one-line summary to the user: `N ideas accepted, K skipped. Written to Prompts/brainstorm.md.`

4. If any accepted idea looks ready to become a Todo item, suggest: `Promote idea M to implementation.md? Then /plan-convert it into a canvas.`

## Anti-patterns

- **Don't batch ideas** — one per turn, always.
- **Don't propose ideas already in `Prompts/brainstorm.md`** — check first.
- **Don't ignore the discovery answers** — they're constraints, not suggestions.
- **Don't go generic** — every idea must cite something concrete from this project or the input files.
- **Don't keep going after `stop`** — end cleanly, save what's been accepted.
- **Don't fabricate to fill the hard cap** — if you run out of grounded ideas, say so and jump to Phase 4 early.
