---
name: pigx-pipelines
description: PiGx genomics pipelines. Configure and run reproducible Guix-based pipelines for scRNA-seq, ChIP-seq, BS-seq, and RNA-seq with YAML sample sheets, automatic QC reports, and Snakemake backends.
license: MIT license
metadata:
    skill-author: VFranke
---

# PiGx: PIpelines in Genomics

## Overview

PiGx (PIpelines in Genomics) is a collection of reproducible genomics data processing pipelines developed at the Berlin Institute for Medical Systems Biology (BIMSB) at the Max Delbruck Center (MDC Berlin), primarily by the Akalin lab. Each pipeline takes raw sequencing reads, processes them through established bioinformatics tools, and produces analysis results together with comprehensive HTML reports.

PiGx pipelines share a common design philosophy:

- **Reproducibility through GNU Guix**: Every pipeline is packaged as a Guix package, pinning all software dependencies down to the compiler and library versions. This guarantees bit-for-bit reproducible results.
- **Snakemake backend**: All pipelines use Snakemake as the workflow engine, providing automatic dependency resolution, parallelization, and cluster submission support.
- **Declarative configuration**: Each run is defined by two files -- a `settings.yaml` for pipeline parameters and a `sample_sheet.csv` (or `.yaml`) describing the samples.
- **Automatic QC reports**: Every pipeline generates self-contained HTML reports with quality metrics, summary statistics, and interactive visualizations.

**Available pipelines:**

| Pipeline | Assay | Key tools |
|----------|-------|-----------|
| `pigx scrnaseq` | Single-cell RNA-seq | STARsolo / Cell Ranger, Seurat, SingleCellExperiment, scran |
| `pigx chipseq` | ChIP-seq | Bowtie2, MACS2, GenomicRanges, DiffBind |
| `pigx bsseq` | Bisulfite sequencing | Bismark, methylKit, genomation |
| `pigx rnaseq` | Bulk RNA-seq | STAR, featureCounts (Subread), DESeq2 |

## When to Use This Skill

Use this skill when:

- **Setting up a PiGx pipeline run**: "configure pigx scrnaseq for my 10X samples", "write a sample sheet for pigx chipseq"
- **Writing configuration files**: "create settings.yaml for pigx rnaseq", "set genome reference paths"
- **Troubleshooting pipeline errors**: "pigx bsseq fails at trimming step", "Snakemake rule error in pigx chipseq"
- **Understanding pipeline outputs**: "where are the BAM files from pigx rnaseq", "how to find the count matrix from pigx scrnaseq"
- **Customizing pipeline behavior**: "add a custom Snakemake rule to pigx chipseq", "override MACS2 parameters"
- **Installing via Guix**: "install pigx scrnaseq with guix", "set up Guix environment for pigx"
- **Interpreting QC reports**: "what does the fingerprint plot in the pigx chipseq report mean"

## Quick Start

### 1. Install via GNU Guix

```bash
# Install a specific pipeline
guix install pigx-scrnaseq
guix install pigx-chipseq
guix install pigx-bsseq
guix install pigx-rnaseq

# Or use guix environment for a transient shell
guix shell pigx-rnaseq
```

### 2. Prepare Configuration Files

Every PiGx pipeline requires two input files:

**sample_sheet.csv** -- describes your samples:
```csv
name,reads,reads2,sample_type
treatment_rep1,/data/reads/treat1_R1.fq.gz,/data/reads/treat1_R2.fq.gz,treatment
treatment_rep2,/data/reads/treat2_R1.fq.gz,/data/reads/treat2_R2.fq.gz,treatment
control_rep1,/data/reads/ctrl1_R1.fq.gz,/data/reads/ctrl1_R2.fq.gz,control
```

**settings.yaml** -- pipeline parameters and paths:
```yaml
locations:
  output-dir: /results/rnaseq_run1
  genome-fasta: /genomes/mm10/genome.fa
  gtf-file: /genomes/mm10/genes.gtf
  reads-dir: /data/reads

execution:
  submit-to-cluster: no
  jobs: 8
  nice: 19
```

### 3. Run the Pipeline

```bash
pigx rnaseq -s settings.yaml sample_sheet.csv
```

The pipeline will create the output directory, run all steps through Snakemake, and generate HTML reports when complete.

## Core Pipelines

### pigx scrnaseq -- Single-Cell RNA-seq

The scRNA-seq pipeline processes droplet-based single-cell data (10X Genomics Chromium and similar) from raw FASTQ files to a fully annotated count matrix and downstream analysis.

**Processing steps:**

1. **Read mapping**: STARsolo (or Cell Ranger if configured) for barcode-aware alignment and UMI counting
2. **Quality control**: Cell filtering based on UMI counts, detected genes, and mitochondrial content
3. **Count matrix generation**: Sparse gene-by-cell count matrix (raw and filtered)
4. **Normalization and clustering**: Seurat or SingleCellExperiment/scran-based normalization, PCA, UMAP, and graph-based clustering
5. **Reporting**: HTML report with knee plots, QC violin plots, UMAP embeddings, and marker gene tables

**Sample sheet columns for scRNA-seq:**

| Column | Description |
|--------|-------------|
| `name` | Unique sample identifier |
| `reads` | Path to Read 1 FASTQ (cell barcode + UMI) |
| `reads2` | Path to Read 2 FASTQ (cDNA insert) |
| `sample_type` | Group label (e.g., treatment, control) |

**Settings specific to scRNA-seq:**

```yaml
locations:
  output-dir: /results/scrnaseq
  genome-fasta: /genomes/mm10/genome.fa
  gtf-file: /genomes/mm10/genes.gtf
  reads-dir: /data/reads

scrnaseq:
  cell-barcode-length: 16
  umi-length: 12
  chemistry: "10XV3"       # 10XV2, 10XV3, or custom
  mapper: "STARsolo"       # STARsolo or CellRanger

execution:
  jobs: 16
```

**Run:**
```bash
pigx scrnaseq -s settings.yaml sample_sheet.csv
```

**Key outputs:**
- `mapped/` -- BAM files with cell barcode and UMI tags
- `analysis/` -- filtered count matrices (MEX format), Seurat objects (.rds), UMAP coordinates
- `report/` -- HTML reports with QC plots and clustering results

### pigx chipseq -- ChIP-seq

The ChIP-seq pipeline handles read mapping, peak calling, quality assessment, and differential binding analysis.

**Processing steps:**

1. **Read trimming**: Adapter removal with Trim Galore
2. **Read mapping**: Bowtie2 alignment to reference genome
3. **Quality control**: FastQC, library complexity, fragment size distribution, fingerprint plots (plotFingerprint)
4. **Peak calling**: MACS2 narrow or broad peak calling with control samples
5. **Peak annotation**: Annotating peaks to nearest genes and genomic features
6. **Differential binding**: DiffBind-based analysis when replicates and conditions are provided
7. **Reporting**: Comprehensive HTML report with all QC metrics, peak statistics, and heatmaps

**Sample sheet columns for ChIP-seq:**

| Column | Description |
|--------|-------------|
| `name` | Unique sample identifier |
| `reads` | Path to Read 1 FASTQ |
| `reads2` | Path to Read 2 FASTQ (paired-end) or leave empty for SE |
| `sample_type` | ChIP target (e.g., H3K4me3, H3K27ac) |
| `control` | Name of the corresponding input/IgG sample |

**Settings specific to ChIP-seq:**

```yaml
locations:
  output-dir: /results/chipseq
  genome-fasta: /genomes/hg38/genome.fa
  gtf-file: /genomes/hg38/genes.gtf
  reads-dir: /data/reads

general:
  assembly: "hg38"
  effective-genome-size: 2913022398

chipseq:
  peak-calling:
    method: "macs2"
    qvalue: 0.05
    broad: no            # set to yes for H3K27me3, H3K36me3, etc.
    extra-args: ""       # additional MACS2 arguments

execution:
  jobs: 8
```

**Run:**
```bash
pigx chipseq -s settings.yaml sample_sheet.csv
```

**Key outputs:**
- `mapped/` -- sorted, deduplicated BAM files and indices
- `analysis/peaks/` -- MACS2 peak files (.narrowPeak or .broadPeak)
- `analysis/diffbind/` -- differential binding results (if applicable)
- `report/` -- HTML report with QC, peak stats, genomic annotation plots

### pigx bsseq -- Bisulfite Sequencing

The BS-seq pipeline processes whole-genome bisulfite sequencing (WGBS) or reduced-representation bisulfite sequencing (RRBS) data to generate single-base methylation calls and differential methylation analysis.

**Processing steps:**

1. **Read trimming**: Trim Galore with RRBS-aware trimming when applicable
2. **Bisulfite mapping**: Bismark alignment (Bowtie2 backend)
3. **Deduplication**: Bismark deduplication for WGBS (skipped for RRBS)
4. **Methylation extraction**: Per-base methylation levels (CpG, CHG, CHH contexts)
5. **Segmentation and DMR calling**: methylKit for differential methylation analysis
6. **Annotation**: genomation for annotating DMRs to genomic features (promoters, exons, introns, intergenic)
7. **Reporting**: HTML report with global methylation statistics, coverage histograms, PCA of methylation profiles, and DMR summaries

**Sample sheet columns for BS-seq:**

| Column | Description |
|--------|-------------|
| `name` | Unique sample identifier |
| `reads` | Path to Read 1 FASTQ |
| `reads2` | Path to Read 2 FASTQ (paired-end) or leave empty for SE |
| `sample_type` | Group label (e.g., tumor, normal) |
| `protocol` | `WGBS` or `RRBS` |

**Settings specific to BS-seq:**

```yaml
locations:
  output-dir: /results/bsseq
  genome-fasta: /genomes/hg38/genome.fa
  reads-dir: /data/reads

general:
  assembly: "hg38"

bsseq:
  bismark:
    extra-args: ""
  methylkit:
    min-coverage: 10
    difference: 25       # minimum percent methylation difference
    qvalue: 0.01
  context: "CpG"         # CpG, CHG, or CHH

execution:
  jobs: 8
```

**Run:**
```bash
pigx bsseq -s settings.yaml sample_sheet.csv
```

**Key outputs:**
- `mapped/` -- Bismark BAM files
- `analysis/methylation/` -- per-base methylation calls (.cov files)
- `analysis/differential/` -- DMR tables and annotated results
- `report/` -- HTML report with methylation profiles, coverage, PCA, and DMR summaries

### pigx rnaseq -- Bulk RNA-seq

The RNA-seq pipeline performs read mapping, gene quantification, and differential expression analysis.

**Processing steps:**

1. **Read trimming**: Trim Galore adapter and quality trimming
2. **Read mapping**: STAR two-pass alignment to reference genome
3. **Quantification**: featureCounts (Subread) for gene-level read counts
4. **Quality control**: FastQC, mapping statistics, gene body coverage, read distribution
5. **Differential expression**: DESeq2 analysis when sample groups are defined
6. **Reporting**: HTML report with QC metrics, PCA, sample correlation, MA plots, volcano plots, and DE gene tables

**Sample sheet columns for RNA-seq:**

| Column | Description |
|--------|-------------|
| `name` | Unique sample identifier |
| `reads` | Path to Read 1 FASTQ |
| `reads2` | Path to Read 2 FASTQ (paired-end) or leave empty for SE |
| `sample_type` | Group label for differential expression (e.g., treatment, control) |

**Settings specific to RNA-seq:**

```yaml
locations:
  output-dir: /results/rnaseq
  genome-fasta: /genomes/mm10/genome.fa
  gtf-file: /genomes/mm10/genes.gtf
  reads-dir: /data/reads

general:
  assembly: "mm10"
  strandedness: "reverse"   # none, forward, reverse

rnaseq:
  star:
    extra-args: ""
  featurecounts:
    extra-args: ""
  deseq2:
    alpha: 0.05
    lfc-threshold: 0

execution:
  jobs: 8
```

**Run:**
```bash
pigx rnaseq -s settings.yaml sample_sheet.csv
```

**Key outputs:**
- `mapped/` -- STAR-aligned, sorted BAM files
- `analysis/counts/` -- raw count matrix (genes x samples)
- `analysis/deseq2/` -- normalized counts, DE results tables, rlog-transformed data
- `report/` -- HTML report with full QC and DE analysis results

## Configuration Reference

### settings.yaml Structure

All PiGx pipelines share a common settings.yaml structure with pipeline-specific additions:

```yaml
# === Shared sections ===

locations:
  output-dir: /path/to/output          # Required: where results are written
  genome-fasta: /path/to/genome.fa      # Required: reference genome FASTA
  gtf-file: /path/to/genes.gtf          # Required for most pipelines
  reads-dir: /path/to/reads             # Optional: prefix for relative FASTQ paths

general:
  assembly: "hg38"                       # Genome assembly name
  strandedness: "none"                   # Library strandedness (RNA-seq)

execution:
  submit-to-cluster: no                  # yes to submit via cluster (e.g., SLURM)
  jobs: 4                                # Number of parallel Snakemake jobs
  nice: 19                               # Process niceness
  cluster:
    memory: "8G"                         # Memory per job (cluster mode)
    queue: "short"                       # Cluster queue name
    args: ""                             # Additional cluster submission arguments

# === Pipeline-specific section ===
# Add a section named after the pipeline (chipseq, rnaseq, bsseq, scrnaseq)
# with tool-specific parameters as shown in the pipeline sections above.
```

**Important notes on settings.yaml:**

- All paths can be absolute or relative to the working directory.
- The `reads-dir` path is prepended to FASTQ paths in the sample sheet if those paths are relative.
- The `output-dir` is created automatically if it does not exist.
- Tool paths are generally not needed when running through Guix, as they are resolved from the package environment.

### sample_sheet.csv Format

The sample sheet is a CSV file with a mandatory header row. The exact columns vary by pipeline, but these are always present:

| Column | Required | Description |
|--------|----------|-------------|
| `name` | Yes | Unique sample identifier (no spaces, no special characters) |
| `reads` | Yes | Path to Read 1 FASTQ (absolute or relative to reads-dir) |
| `reads2` | No | Path to Read 2 FASTQ (omit or leave empty for single-end) |
| `sample_type` | Yes | Group label used for comparisons and report grouping |

Additional columns depend on the pipeline (e.g., `control` for ChIP-seq, `protocol` for BS-seq).

**Example (ChIP-seq with input controls):**

```csv
name,reads,reads2,sample_type,control
H3K4me3_rep1,h3k4_r1_R1.fq.gz,h3k4_r1_R2.fq.gz,H3K4me3,Input_rep1
H3K4me3_rep2,h3k4_r2_R1.fq.gz,h3k4_r2_R2.fq.gz,H3K4me3,Input_rep2
Input_rep1,input_r1_R1.fq.gz,input_r1_R2.fq.gz,Input,
Input_rep2,input_r2_R1.fq.gz,input_r2_R2.fq.gz,Input,
```

## Output Directory Structure

All PiGx pipelines produce a consistent output layout:

```
output-dir/
  mapped/                 # Aligned BAM/CRAM files and indices
  analysis/               # Pipeline-specific analysis results
    counts/               # (rnaseq) count matrices
    peaks/                # (chipseq) peak call files
    methylation/          # (bsseq) methylation call files
    deseq2/               # (rnaseq) differential expression
    diffbind/             # (chipseq) differential binding
    differential/         # (bsseq) differential methylation
    seurat/               # (scrnaseq) Seurat objects
  report/                 # HTML reports and associated figures
  trimmed/                # Trimmed FASTQ files (intermediate)
  logs/                   # Snakemake and tool log files
  benchmarks/             # Snakemake benchmark files (runtime, memory)
```

## Guix Integration

PiGx pipelines are first-class Guix packages. This provides unique advantages:

### Full Reproducibility

Every dependency -- from the C compiler to R packages to command-line tools -- is pinned by its cryptographic hash. Two users running the same Guix commit will get identical software environments.

```bash
# Show exact package provenance
guix describe

# Create a reproducible manifest
guix describe -f channels > channels.scm

# Reproduce the environment later or on another machine
guix time-machine -C channels.scm -- shell pigx-rnaseq
```

### Installation

```bash
# Install permanently into your profile
guix install pigx-rnaseq pigx-chipseq pigx-bsseq pigx-scrnaseq

# Or use a transient shell (nothing installed permanently)
guix shell pigx-rnaseq -- pigx rnaseq -s settings.yaml sample_sheet.csv

# Use a Guix manifest for a project
guix shell -m manifest.scm
```

**Example manifest.scm:**
```scheme
(specifications->manifest
  '("pigx-rnaseq"
    "pigx-chipseq"
    "samtools"
    "r-tidyverse"))
```

### Guix Environment Activation

When using Guix profiles or `guix shell`, all tool paths are automatically resolved. You do not need to set tool paths manually in `settings.yaml`.

```bash
# Activate a Guix profile containing pigx
export GUIX_PROFILE="$HOME/.guix-extra-profiles/pigx"
source "$GUIX_PROFILE/etc/profile"

# Now pigx commands are on your PATH
pigx rnaseq -s settings.yaml sample_sheet.csv
```

## Running PiGx Pipelines

### Basic Invocation

```bash
pigx <pipeline> [options] -s settings.yaml sample_sheet.csv
```

**Common options:**

| Option | Description |
|--------|-------------|
| `-s, --settings` | Path to settings.yaml |
| `-n, --dry-run` | Show what would be executed without running anything |
| `-j, --jobs` | Override the number of parallel jobs |
| `--forceall` | Force re-run of all steps |
| `--target` | Run only up to a specific Snakemake target |
| `--printshellcmds` | Print the shell commands being executed |

### Dry Run (Recommended First Step)

Always perform a dry run before a full execution to verify the configuration:

```bash
pigx rnaseq -s settings.yaml sample_sheet.csv -n
```

This prints the Snakemake execution plan without running any jobs.

### Cluster Execution

PiGx supports submitting jobs to HPC clusters via Snakemake's cluster integration:

```yaml
execution:
  submit-to-cluster: yes
  jobs: 100
  cluster:
    memory: "16G"
    queue: "long"
    args: "--time=24:00:00"
```

For SLURM clusters, Snakemake will generate `sbatch` commands for each rule.

## Customization

### Overriding Pipeline Parameters

Tool-specific parameters can be passed through the `extra-args` fields in settings.yaml:

```yaml
chipseq:
  peak-calling:
    extra-args: "--nomodel --shift -100 --extsize 200"

rnaseq:
  star:
    extra-args: "--outFilterMismatchNmax 10 --alignIntronMax 500000"
```

### Adding Custom Snakemake Rules

PiGx pipelines are Snakemake workflows. You can extend them by creating additional Snakefiles that reference PiGx output files:

```python
# custom_rules.snakefile
# This file extends the pigx pipeline with custom post-processing

rule custom_peak_annotation:
    input:
        peaks="analysis/peaks/{sample}_peaks.narrowPeak",
        gtf=config["locations"]["gtf-file"]
    output:
        "analysis/custom/{sample}_annotated_peaks.tsv"
    shell:
        """
        annotatePeaks.pl {input.peaks} hg38 -gtf {input.gtf} > {output}
        """
```

Run the extended pipeline:

```bash
snakemake -s custom_rules.snakefile --configfile settings.yaml
```

### Resuming Failed Runs

Because PiGx uses Snakemake, failed runs can be resumed from where they stopped:

```bash
# Simply re-run the same command; completed steps are skipped
pigx rnaseq -s settings.yaml sample_sheet.csv
```

To force re-execution of specific steps:

```bash
# Rerun everything from scratch
pigx rnaseq -s settings.yaml sample_sheet.csv --forceall

# Rerun only rules that depend on a particular file
pigx rnaseq -s settings.yaml sample_sheet.csv --forcerun star_align
```

## Key Concepts

### Sample Sheet Format Rules

- The file must be valid CSV with a header row.
- Sample names must be unique and contain only alphanumeric characters, hyphens, and underscores. No spaces.
- FASTQ paths can be absolute or relative to the `reads-dir` specified in settings.yaml.
- For single-end data, leave the `reads2` column empty (do not omit the column entirely).
- The `sample_type` column is used for grouping in differential analyses and QC reports.

### Settings YAML Structure

- YAML keys use lowercase with hyphens (e.g., `output-dir`, `genome-fasta`).
- Boolean values: use `yes`/`no` (YAML 1.1 style) or `true`/`false`.
- The `locations` section is shared across all pipelines.
- The `execution` section controls Snakemake parallelism and cluster submission.
- Pipeline-specific sections are named after the pipeline command (e.g., `rnaseq`, `chipseq`).

### Reproducibility via Guix

- PiGx pipelines are designed to be run inside Guix-managed environments.
- The Guix channel commit determines the exact versions of all tools.
- Save `guix describe` output alongside your results for full provenance.
- Use `guix time-machine` to reproduce an analysis months or years later.
- The combination of settings.yaml + sample_sheet.csv + Guix channel commit fully specifies a reproducible analysis.

## Common Pitfalls

### YAML Formatting Errors

**Problem:** Pipeline fails at startup with a YAML parsing error.

**Causes and fixes:**
- Indentation must use spaces, never tabs. Use exactly 2 spaces per level.
- Strings containing colons or special characters must be quoted: `assembly: "hg38"`.
- Boolean values `yes`/`no` can be misinterpreted. When in doubt, quote them or use `true`/`false`.
- Trailing whitespace after values can cause subtle issues.

```yaml
# WRONG -- tab indentation
locations:
	output-dir: /results    # uses tab

# CORRECT -- space indentation
locations:
  output-dir: /results      # uses 2 spaces
```

### Sample Sheet Column Name Errors

**Problem:** Pipeline runs but produces no output or wrong groupings.

**Causes and fixes:**
- Column names are case-sensitive. Use exactly `name`, `reads`, `reads2`, `sample_type`.
- Do not add extra whitespace around column names or values.
- Do not use Excel-generated CSV files without checking for BOM markers or encoding issues. Save as UTF-8 CSV.
- If `reads2` is not applicable, keep the column header but leave the values empty.

```csv
# WRONG
Name,Reads,Sample_Type
sample1,reads.fq.gz,treatment

# CORRECT
name,reads,sample_type
sample1,reads.fq.gz,treatment
```

### Genome Index Path Issues

**Problem:** Pipeline fails at the mapping step with "index not found" or takes unexpectedly long (building index from scratch).

**Causes and fixes:**
- STAR, Bowtie2, and Bismark indices must be pre-built and accessible. PiGx will attempt to build them if missing, which is time-consuming and requires significant memory.
- Verify that the genome FASTA path in settings.yaml matches the path used when building the index.
- For STAR, the index directory must contain `Genome`, `SA`, `SAindex`, and related files.
- For Bowtie2, the `.bt2` index files must be in the same directory as or alongside the genome FASTA.
- Ensure file permissions allow read access to all index files.

### Guix Environment Not Activated

**Problem:** `pigx: command not found` or tools within the pipeline fail with "command not found."

**Causes and fixes:**
- Ensure you have sourced the Guix profile: `source $GUIX_PROFILE/etc/profile`.
- If using `guix shell`, run the pipeline inside the shell session: `guix shell pigx-rnaseq -- pigx rnaseq ...`.
- Check that the Guix daemon is running: `sudo herd status guix-daemon` (Guix System) or check the systemd service.
- On foreign distributions (Ubuntu, CentOS), ensure `/gnu/store` is accessible and the Guix binary is on your PATH.

### Insufficient Disk Space or Memory

**Problem:** Pipeline fails mid-run with cryptic errors, often during STAR mapping or index building.

**Causes and fixes:**
- STAR genome index generation requires 30+ GB of RAM for mammalian genomes.
- BAM files from whole-genome experiments can be very large. Ensure the output directory has sufficient disk space (hundreds of GB for large experiments).
- Set the number of jobs (`-j`) conservatively if running on a shared machine with limited memory.
- Use `--dry-run` first to estimate the number of steps and plan resources.

### FASTQ File Path Mismatches

**Problem:** Pipeline reports missing input files.

**Causes and fixes:**
- If `reads-dir` is set in settings.yaml, FASTQ paths in the sample sheet are resolved relative to it.
- If `reads-dir` is not set, FASTQ paths must be absolute or relative to the working directory.
- Double-check that file names in the sample sheet match the actual file names on disk (case-sensitive on Linux).
- Verify that symlinks, if used, point to valid targets.

## Example: Complete RNA-seq Analysis

Below is a complete example of setting up and running a pigx RNA-seq analysis.

**1. Create sample_sheet.csv:**

```csv
name,reads,reads2,sample_type
wildtype_rep1,wt_rep1_R1.fq.gz,wt_rep1_R2.fq.gz,wildtype
wildtype_rep2,wt_rep2_R1.fq.gz,wt_rep2_R2.fq.gz,wildtype
wildtype_rep3,wt_rep3_R1.fq.gz,wt_rep3_R2.fq.gz,wildtype
knockout_rep1,ko_rep1_R1.fq.gz,ko_rep1_R2.fq.gz,knockout
knockout_rep2,ko_rep2_R1.fq.gz,ko_rep2_R2.fq.gz,knockout
knockout_rep3,ko_rep3_R1.fq.gz,ko_rep3_R2.fq.gz,knockout
```

**2. Create settings.yaml:**

```yaml
locations:
  output-dir: /results/rnaseq_wt_vs_ko
  genome-fasta: /genomes/mm10/GRCm38.primary_assembly.genome.fa
  gtf-file: /genomes/mm10/gencode.vM25.annotation.gtf
  reads-dir: /data/fastq/rnaseq

general:
  assembly: "mm10"
  strandedness: "reverse"

rnaseq:
  star:
    extra-args: ""
  featurecounts:
    extra-args: ""
  deseq2:
    alpha: 0.05
    lfc-threshold: 0

execution:
  jobs: 16
  nice: 19
```

**3. Dry run to verify configuration:**

```bash
guix shell pigx-rnaseq -- pigx rnaseq -s settings.yaml sample_sheet.csv -n
```

**4. Execute:**

```bash
guix shell pigx-rnaseq -- pigx rnaseq -s settings.yaml sample_sheet.csv
```

**5. Examine results:**

```
/results/rnaseq_wt_vs_ko/
  mapped/
    wildtype_rep1.sorted.bam
    wildtype_rep1.sorted.bam.bai
    ...
  analysis/
    counts/
      raw_counts.tsv          # Gene-by-sample count matrix
    deseq2/
      wildtype_vs_knockout.tsv # DE results with log2FC, padj
      normalized_counts.tsv    # DESeq2-normalized counts
  report/
    index.html                 # Main QC and analysis report
  logs/
    star_wildtype_rep1.log
    ...
```

## Handling User Requests

### For Configuration Help

1. Ask which pipeline (scrnaseq, chipseq, bsseq, rnaseq) the user needs.
2. Ask about the organism and genome assembly.
3. Generate a settings.yaml with appropriate defaults.
4. Generate a sample_sheet.csv template with the correct columns for that pipeline.
5. Recommend a dry run before full execution.

### For Troubleshooting

1. Ask the user to share the error message and the log file from the `logs/` directory.
2. Check settings.yaml for path and formatting issues.
3. Check sample_sheet.csv for column names and file path correctness.
4. Verify that the Guix environment is active and the correct pipeline is installed.
5. Check disk space and memory availability.

### For Output Interpretation

1. Point the user to the HTML report in the `report/` directory for an overview.
2. For programmatic access, direct them to the relevant files in `analysis/`.
3. Explain the meaning of key QC metrics (mapping rate, duplication, library complexity).
4. For differential results, explain the columns (log2FoldChange, padj, baseMean).
