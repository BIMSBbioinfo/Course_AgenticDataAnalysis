---
name: kanban
description: Cross-project task board. Scans ~/Projects/, finds Claude-managed projects, and writes a unified kanban plus 3 lane files (todo/wip/done) to ~/Utils/kanban_<yymmdd>{,_todo,_wip,_done}.md for side-by-side viewing in vim. Use when the user wants an overview of open tasks across all projects.
argument-hint: [projects-root]
allowed-tools: Read, Write, Bash(find *), Bash(grep *), Bash(sed *), Bash(awk *), Bash(git *), Bash(date *), Bash(basename *), Bash(dirname *), Bash(ls *), Bash(stat *), Bash(mkdir *)
---

# /kanban — Cross-Project Task Board

Scan all Claude-managed projects, extract task state, and write a unified kanban plus three lane files for vim side-by-side viewing.

## Configuration

- **Projects root**: `$ARGUMENTS` if provided, else `$HOME/Projects`
- **Output directory**: `$HOME/Utils` (create if missing)
- **Date stamp**: `today=$(date +%y%m%d)`
- **Stale cutoff**: skip projects whose plan hasn't been touched in 90+ days
- **Done window**: only show items completed in the last 14 days in the Done lane

## Phase 1: Discover Claude Projects

Find candidate projects:

    # Primary signal: implementation plan
    find "$root" -mindepth 2 -maxdepth 4 -path "*/Prompts/implementation_plan.md" 2>/dev/null

    # Fallback signal: CLAUDE.md (project root, not plugin/skill dirs)
    find "$root" -mindepth 2 -maxdepth 3 -name CLAUDE.md \
        -not -path "*/.claude/*" -not -path "*/skills/*" 2>/dev/null

Project name = the directory two levels above the plan (`<root>/<project>/Prompts/implementation_plan.md`) or the directory containing `CLAUDE.md`.

Filter: drop projects whose plan/CLAUDE.md mtime is older than 90 days.

## Phase 2: Extract Tasks

For each project's `implementation_plan.md`:

    todo:  grep -E '^- \[ \]' "$plan"
    wip:   grep -E '^- \[~\]' "$plan"     # convention: ~ = in progress
    done:  grep -E '^- \[x\]' "$plan"

Strip the checkbox prefix and truncate each task line to ~100 chars.

Last-touched date for each project:

    git -C "$proj_dir" log -1 --format=%cs -- "$plan" 2>/dev/null \
        || stat -c %y "$plan" | cut -d' ' -f1

For projects with only `CLAUDE.md` (no plan): surface with a `*No implementation plan*` placeholder in the To Do lane.

For the Done lane, filter to items completed in the last 14 days when possible. If `git log -p` shows when each `[x]` was set, use that; otherwise include the full Done list and note the limitation.

## Phase 3: Render Files

### 3a. Unified file: `$HOME/Utils/kanban_<today>.md`

    # Kanban — <YYYY-MM-DD>

    ## Summary

    | Project | Last touched | TODO | WIP | DONE |
    |---|---|---:|---:|---:|
    | AAkalin_Neuroblastoma | 2026-05-04 | 3 | 1 | 12 |
    | AAkalin_Urine | 2026-04-22 | 5 | 0 | 8 |
    ...

    ## To Do

    ### AAkalin_Neuroblastoma
    - Compute MES signature on cohort B
    - Cluster cell lines by ADRN/MES

    ### AAkalin_Urine
    - Background subtraction QC
    ...

    ## In Progress

    ### AAkalin_Neuroblastoma
    - Refactor scoring helpers

    ## Done (last 14 days)

    ### AAkalin_Neuroblastoma
    - Initial DE analysis
    ...

### 3b. Lane files: `kanban_<today>_todo.md`, `kanban_<today>_wip.md`, `kanban_<today>_done.md`

Each is the corresponding section from the unified file, scoped to one lane only. Header reflects the lane:

    # To Do — <YYYY-MM-DD>

    ## AAkalin_Neuroblastoma
    - Compute MES signature on cohort B
    - Cluster cell lines by ADRN/MES

    ## AAkalin_Urine
    - Background subtraction QC

Sort projects by **last-touched descending** so the most active work is on top.

## Phase 4: Confirm

Print to stdout:

1. One-line per project: `<project>  TODO:N WIP:N DONE:N  (last: YYYY-MM-DD)`
2. Output paths (unified + 3 lane files)
3. Hint: `kanban <today>` (or just `kanban`) opens the three lanes side-by-side in vim

## Edge cases

- **Non-standard checkboxes**: widen regex to `^[-*] \[[ x~]\]` and warn the user if any project uses unusual formats
- **Missing `~/Projects`**: error out with a clear message
- **No Claude projects found**: write an empty kanban with a note, still create lane files (so the bash function doesn't fail)
- **Empty lane**: write `*No items*` in the lane file rather than leaving it empty
