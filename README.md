# Course: Agentic Data Analysis

Course materials for the **Agentic Genomics Berlin** course (MDC / BIMSB, 2026-05), focused on
combining classical Bash workflows with LLMs and agent-based tooling for bioinformatics
data analysis.

## Contents

### Course materials

- `bioinformatics-quiz.html` — interactive student quiz on Bash, LLMs, and agents.
- `bioinformatics-quiz-answer-key.html` — instructor answer key for the same quiz.

Open either HTML file directly in a browser to view it.

### `.claude/` — Claude Code configuration

A project-scoped [Claude Code](https://docs.claude.com/en/docs/claude-code) setup
used during the course. Originally a separate repo at
`github.com/frenkiboy/.claude`; vendored here so students get the same
agent environment with a single clone.

- `CLAUDE.md` — top-level instruction: prefer existing skills over building from scratch.
- `settings.json` — permission allowlist (R, Python, common Unix tools, genomics CLIs
  like `samtools`, `bedtools`, `snakemake`, `guix`, `tmux`), plugin and hook config,
  status-line command. Note: `statusLine.command` points at a Linux path
  (`/home/vfranke/.claude/statusline.sh`) and should be adjusted per machine.
- `statusline.sh` — custom Claude Code status-line script.
- `commands/` — custom slash commands: `gogogo`, `grill-me`, `plan-convert`,
  `plan-exec`, `plan-review`, `report`, `triage`, `wup`,
  `research-to-implementation`, `evaluate-plan`.
- `skills/` — 44 bioinformatics-oriented skills covering pipelines (Snakemake,
  PiGx, STAR, Slurm, Guix, tmux), single-cell (scanpy, scvi-tools, anndata,
  cellxgene-census, 10x), bulk RNA-seq / DE (pydeseq2, r-bioconductor),
  genomics utilities (samtools-bedtools, pysam, deeptools, genomic-coordinates,
  ucsc-track-hubs), databases (Ensembl, KEGG, Reactome, STRING, GEO, NCBI Gene,
  PubMed), data libraries (biopython, gget, networkx, zarr, scikit-learn,
  statsmodels), visualization (matplotlib, seaborn, plotly,
  scientific-visualization, scientific-schematics), writing
  (scientific-writing, literature-review), and project scaffolding
  (research-setup, brainstorm, getinfo, karpathy-guidelines, kanban).
- `scripts/` — helper scripts: `install-project-hooks.py`, `prompt-log.py`,
  and a `project-settings-template.json`.
- `plugins/` — Claude Code plugin state (runtime caches gitignored).
- `.gitignore` — excludes credentials, session history, debug/cache/telemetry,
  todos/tasks/plans, conversation logs, and plugin runtime state.

## Tutorial: the prompt-driven workflow

These five commands form a small pipeline that takes a project from "empty
folder" to "committed, reproducible analysis". The unifying idea: the
**prompt** (canvas) is locked down *before* code is written, so every
figure can be walked back to the user request that produced it.

```
/research-setup ─► /brainstorm ─► /grill-me ─► /plan-convert ─► /plan-exec
   scaffold        ideate         resolve         intent              code
                                  TBDs            (canvas)            + commit
```

### 1. `/research-setup` — scaffold a new project

Two modes:

- `/research-setup print` — drops three templates in the current folder
  and stops: `Prompts/research_plan.md`, `CLAUDE.md`, `PIPELINE.md`. Use
  this when you just want the templates inside an existing repo.
- `/research-setup <project-name>` — full scaffold. Claude will ask you
  for `home_folder`, `data_folder`, and `sample_sheet`, then create the
  standard folder layout (`Scripts/Bin/`, `Scripts/Reports/`, `Results/`,
  `Documentation/`, `Prompts/canvases/`, `Prompts/Logs/`), symlink
  `Data/` to your data drive, init `git`, set up R + Python envs, install
  the project-scoped logging hooks (`PROMPT_LOG.md`, `RUN_LOG.md`), and
  seed `implementation.md`, `INDEX.md`, `CHANGELOG.md`.

Run this once per project, then fill in `Prompts/research_plan.md` with
your scientific questions, constraints, and positive/negative controls.

### 2. `/brainstorm` — collaborative ideation

```
/brainstorm                          # survey project, then propose ideas
/brainstorm paper.pdf notes.md       # seed with input files
```

Interactive Q&A. Three discovery questions first (**direction**,
**audacity**, **constraints**), then one idea per turn. For each idea
you reply `accept`, `refine <note>`, `skip`, or `stop`. Accepted ideas
are appended to `Prompts/brainstorm.md`. Use this when you want a
sounding-board pass before committing to implementation work.

### 3. `/grill-me` — resolve TBDs before coding

```
/grill-me                                          # grill the whole plan
/grill-me Prompts/canvases/003_de-analysis.md      # one focal canvas
/grill-me Prompts/research_plan.md                 # the constraints
/grill-me controls                                 # one theme, all canvases
```

Socratic interrogation, **one question at a time**, each with a
recommended answer. Reply with `accept` / `override <answer>` / `skip` /
`stop`. Answers are written back into the target file in place — TBDs
become concrete values (thresholds, normalization methods, controls).
Run this *before* `/plan-exec`, because `plan-exec` will halt on any
canvas that still contains `TBD` tokens in its Operations section.

### 4. `/plan-convert` — turn a Todo item into a canvas

```
/plan-convert next             # take the first ## Todo item
/plan-convert 3                # take the 3rd ## Todo item
/plan-convert deseq2           # fuzzy-match
```

Reads one item from `Prompts/implementation.md`, allocates the next
canvas number, and writes `Prompts/canvases/NNN_slug.md` with the
standard sections: **Question**, **Entities**, **Approach**,
**Structure** (Upstream / Downstream / Lives in), **Operations**
(5–10 numbered steps), **Safeguards** (including a `Done = ...` line).
Unspecified parameters are written as `TBD — confirm with user` rather
than guessed. The item is moved from `## Todo` to `## In progress` with
a `→ Prompts/canvases/NNN_slug.md` backlink. **No code is generated
yet** — that's the next step.

### 5. `/plan-exec` — implement the canvas and commit

```
/plan-exec                          # ask which items to run
/plan-exec next                     # first uncompleted item
/plan-exec 3                        # task 3
/plan-exec 1,3,5                    # selected items
/plan-exec Prompts/my_plan.md all   # alternative plan file
```

For each selected item: if a canvas is linked, its **Operations** become
the step list and its **Safeguards** become the acceptance test. Claude
writes `Scripts/Bin/<name>.{R,py,sh}` transformations and
`Scripts/Reports/NN_<name>.Rmd` reports, marks the item Done, updates
`CHANGELOG.md`, and creates a single commit with an `Implements:
Prompts/canvases/NNN_slug.md` trailer — that trailer is what closes the
provenance chain from figure → canvas → prompt → commit.

### Typical session

```text
/research-setup MyProject                          # one-time scaffold
# … fill in Prompts/research_plan.md …
/brainstorm                                        # ideate new analyses
/triage                                            # promote prompts to Todo
/grill-me Prompts/research_plan.md                 # tighten constraints
/plan-convert next                                 # Todo  → canvas
/grill-me Prompts/canvases/001_*.md                # resolve canvas TBDs
/plan-exec next                                    # canvas → code + commit
```

## Repository

<https://github.com/BIMSBbioinfo/Course_AgenticDataAnalysis>
