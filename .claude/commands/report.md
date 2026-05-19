---
description: Generate a summary of recent project activity from git log, changelog, and implementation plan
argument-hint: [days | last]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash(git log:*), Bash(git diff:*), Bash(git shortlog:*), Bash(date:*), Bash(mkdir:*), Agent]
---

# Project Activity Report

Generate a concise report of recent project activity. Follow each phase sequentially.

---

## Phase 1: Determine Time Range

Check `$ARGUMENTS`:
- If a **number** is provided (e.g., `7`): report on the last N days
- If `last` is provided: report since the last time this report was generated (check `Prompts/Logs/` for the most recent `yymmdd_report.md`)
- If **no argument**: default to the last 7 days

---

## Phase 2: Gather Activity

Collect information from multiple sources in parallel:

1. **Git log**: `git log --since="N days ago" --oneline --stat` — all commits in the time range
2. **Git diff summary**: `git diff --stat HEAD~20` (or appropriate range) for a file-level overview
3. **CHANGELOG.md**: Read if it exists — extract entries within the time range
4. **Implementation plan**: Read `implementation_plan.md` — identify items marked `[x]` recently (cross-reference with git log dates)
5. **Reports folder**: Check `Scripts/Reports/` for new or modified `.Rmd`/`.qmd` files within the time range
6. **Results folder**: Check `Results/` for new output directories or figures

---

## Phase 3: Compile Report

Write the report to `Prompts/Logs/yymmdd_report.md` with the following structure:

```markdown
# Project Report — YYYY-MM-DD
**Period**: YYYY-MM-DD to YYYY-MM-DD

## Summary
A 2-3 sentence overview of what happened in this period.

## Completed Work
- Bulleted list of completed implementation plan items
- Each with a brief description of what was done

## Reports Updated
- List of reports that were created or modified
- For each: what analyses were added or changed

## New Results
- New figures, tables, or output files generated
- Organized by report/analysis

## Git Activity
- Number of commits
- Files changed summary
- Key contributors (if multiple)

## Next Steps
- Top 3 items to work on next (from implementation plan)
```

---

## Phase 4: Present to User

1. Display the report content directly to the user
2. Confirm the file was saved to `Prompts/Logs/yymmdd_report.md`

---
