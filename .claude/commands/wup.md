---
description: Show status of current Claude session — background tasks, agents, and active plan progress
allowed-tools: [Read, Glob, Grep, Bash(find:*), Bash(ls:*), Bash(stat:*), TaskList]
---

# What's Up — Current Session Status

Show a quick overview of everything happening in this Claude session right now.

---

## Phase 1: Background Tasks & Agents

1. Use `TaskList` to get all tasks in the current session (background shell commands, agents, etc.)
2. For each task, show:
   - Task ID
   - Description / command summary
   - Status (running, completed, failed)
   - If completed: brief result (success/failure)
   - If running: how long it's been running

---

## Phase 2: Active Plan

Check if there's an implementation plan in the current working directory:

1. Look for `implementation_plan.md` in the current directory and `Prompts/` (max depth 2)
2. If found, show:
   - Progress: `[done/total tasks]`
   - Next 3 uncompleted tasks (lines matching `- [ ]`)

If no plan is found, skip this section silently.

---

## Phase 3: Display

Present a compact summary:

```
## Session Tasks
| ID | Description | Status |
|----|-------------|--------|
| ...| ...         | ...    |

## Plan Progress (if any)
**<path>** — [done/total]
  Next:
  - <task 1>
  - <task 2>
  - <task 3>
```

Keep output concise. No extra commentary.
