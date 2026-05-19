---
description: Full cycle - review the implementation plan, then execute all uncompleted items
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Agent]
---

# GOGOGO: Full Plan Review + Execution Cycle

Run `/plan-review` followed by `/plan-exec` in a single session. Do NOT stop between them.

---

## Part 1: Plan Review

Execute all phases from `/plan-review`:

1. **Locate** `implementation_plan.md`
2. **Audit** the codebase with parallel Explore agents to find completed, in-progress, and not-started items
3. **Update** the plan — mark completed items `[x]`, add novel additions
4. **Commit** the updated plan
5. **Propose next steps** — rank top 3-5 items by impact and feasibility
6. **Export tasks** to `Prompts/Logs/yymmdd_tasks.md`
7. **Update implementation summary** — `implementation_summary.md` organized by report

**After completing the review, present the proposed next steps to the user and ask for confirmation before proceeding to execution.** If the user confirms, continue. If the user selects specific items, execute only those.

---

## Part 2: Plan Execution

Execute all phases from `/plan-exec`:

1. **Parse** uncompleted items from the updated plan
2. **Execute** each item — edit reports, scripts, code; mark `[x]` as done
3. **Update changelog** — add dated entry to `CHANGELOG.md`
4. **Commit** all changes with descriptive message
5. **Summary** — report what was done, what was skipped, suggest what's next

---

## Rules

- Do not pause between review and execution unless waiting for user confirmation on which items to execute
- If execution completes all items, run a final review pass to update the summary and tasks files
- Keep the user informed at major milestones but do not over-report
