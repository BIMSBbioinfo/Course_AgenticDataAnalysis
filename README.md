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

## Repository

<https://github.com/BIMSBbioinfo/Course_AgenticDataAnalysis>
