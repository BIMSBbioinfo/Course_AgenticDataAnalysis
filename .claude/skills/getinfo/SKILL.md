---
name: getinfo
description: Quickly survey the current project folder and explain what it's about — data types, analyses, tools, and current state.
allowed-tools: Read, Glob, Grep, Bash(ls *), Bash(head *), Bash(wc *), Bash(tree *), Bash(git log *), Bash(git status *)
---

# Get Info: Project Overview

Your job is to quickly understand what this project is about and present a clear summary to the user.

## Step 1: Survey the Structure

Run these in parallel where possible:

1. `tree -L 2 .` — folder layout
2. Check for key files: `research_plan.md`, `implementation_plan.md`, `README.md`, `CLAUDE.md`, `brainstorm.md`
3. `git log --oneline -10` — recent activity
4. List `Scripts/Reports/` — what reports exist
5. List `Scripts/Bin/` — what shared functions exist
6. List `Results/` — what output has been generated
7. List `Data/` — what data is available
8. Check for `renv.lock`, `environment.yml`, `manifest.scm`, `Snakefile` — computing environment

## Step 2: Read Key Files

Read (first 50 lines is enough) any of these that exist:
- `research_plan.md` or `README.md` — project description
- `implementation_plan.md` — what's planned
- `brainstorm.md` — ideas
- The first report in `Scripts/Reports/` — to understand the analysis

## Step 3: Present Summary

Output a concise summary covering:

- **Project**: What is this project about (1-2 sentences)
- **Data**: What data types are available (RNA-seq, scRNA-seq, clinical, etc.)
- **Analyses done**: List of reports/analyses completed
- **Tools/Environment**: R/Python, key packages, workflow manager
- **Current state**: What's done, what's in progress, what's next
- **Key files**: Where to look for important things

Keep it short and scannable — no more than 30 lines. The user wants a quick orientation, not a deep dive.
