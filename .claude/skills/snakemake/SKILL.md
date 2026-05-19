---
name: snakemake
description: Workflow management for bioinformatics. Define reproducible pipelines with rules, wildcards, and config files. Supports cluster execution (Slurm), conda environments, containers, and modular pipeline design.
license: MIT license
metadata:
    skill-author: VFranke
---

# Snakemake Workflow Management

## 1. Overview

Snakemake is a Python-based workflow management system for building reproducible and scalable data analysis pipelines. It uses a declarative syntax inspired by GNU Make, where you define **rules** that describe how to create output files from input files. Snakemake automatically resolves dependencies between rules, builds a directed acyclic graph (DAG) of jobs, and executes them in the correct order with maximal parallelism.

Snakemake is the de facto standard for bioinformatics pipeline development. It integrates natively with conda environments, Singularity/Apptainer containers, and cluster schedulers such as Slurm. Pipelines written in Snakemake are portable, version-controllable, and inherently documented by their rule definitions.

Key properties:

- **Declarative**: You specify what outputs you want; Snakemake figures out how to produce them.
- **Incremental**: Only out-of-date or missing outputs are recomputed.
- **Scalable**: The same pipeline runs on a laptop or a 1000-node HPC cluster without modification.
- **Reproducible**: Conda environments and containers pin exact software versions per rule.

## 2. When to Use Snakemake

Use Snakemake when:

- You have a multi-step analysis that processes many samples through the same pipeline (RNA-seq, ChIP-seq, scRNA-seq, variant calling, etc.).
- You need reproducibility across environments (local, HPC, cloud).
- Steps have complex dependencies and you want automatic dependency resolution.
- You want incremental re-execution when inputs change or a step fails partway through.
- You need to scale from a few samples to hundreds with no code changes.
- You want integrated conda environment management per rule.

Do NOT use Snakemake when:

- You have a single one-off script with no reuse.
- The workflow is a simple linear two-step process that a shell script handles fine.
- You need real-time streaming or event-driven processing (Snakemake is batch-oriented).

## 3. Quick Start

### Minimal project structure

```
project/
  Snakefile
  config/
    config.yaml
  workflow/
    rules/
      mapping.smk
      qc.smk
    envs/
      star.yaml
    scripts/
      count_reads.py
  samples.tsv
```

### Basic Snakefile

```python
# Snakefile

configfile: "config/config.yaml"

SAMPLES = config["samples"]  # e.g. ["sample_A", "sample_B", "sample_C"]

rule all:
    input:
        expand("results/bam/{sample}.sorted.bam", sample=SAMPLES),
        expand("results/bam/{sample}.sorted.bam.bai", sample=SAMPLES),
        "results/qc/multiqc_report.html"

rule star_align:
    input:
        r1 = "data/fastq/{sample}_R1.fastq.gz",
        r2 = "data/fastq/{sample}_R2.fastq.gz",
        index = config["star_index"]
    output:
        bam = "results/bam/{sample}.Aligned.sortedByCoord.out.bam"
    params:
        out_prefix = "results/bam/{sample}."
    threads: 8
    log:
        "logs/star/{sample}.log"
    shell:
        """
        STAR \
            --runThreadN {threads} \
            --genomeDir {input.index} \
            --readFilesIn {input.r1} {input.r2} \
            --readFilesCommand zcat \
            --outSAMtype BAM SortedByCoordinate \
            --outFileNamePrefix {params.out_prefix} \
            2> {log}
        """

rule sort_and_index:
    input:
        bam = "results/bam/{sample}.Aligned.sortedByCoord.out.bam"
    output:
        bam = "results/bam/{sample}.sorted.bam",
        bai = "results/bam/{sample}.sorted.bam.bai"
    threads: 4
    log:
        "logs/samtools_sort/{sample}.log"
    shell:
        """
        samtools sort -@ {threads} -o {output.bam} {input.bam} 2> {log}
        samtools index -@ {threads} {output.bam} 2>> {log}
        """
```

### Running the pipeline

```bash
# Dry run -- see what would be executed
snakemake -n

# Local execution with 8 cores
snakemake --cores 8

# With conda environments
snakemake --cores 8 --use-conda

# Generate a DAG visualization
snakemake --dag | dot -Tpdf > dag.pdf

# Generate a rulegraph (simplified view)
snakemake --rulegraph | dot -Tpdf > rulegraph.pdf
```

## 4. Core Capabilities

### 4.1 Rules

A rule is the fundamental unit. Each rule has:

- **input**: Files the rule depends on.
- **output**: Files the rule produces.
- **shell** / **script** / **run**: The command or code to execute.
- **params**: Extra parameters that are not files.
- **threads**: CPU cores to request.
- **resources**: Arbitrary resource declarations (mem_mb, gpu, etc.).
- **log**: Log file paths (not auto-deleted on failure).
- **benchmark**: File to record runtime and memory statistics.
- **conda**: Path to a conda environment YAML.
- **container**: Singularity/Apptainer image URL.

```python
rule example:
    input:
        "data/{sample}.fastq.gz"
    output:
        "results/{sample}.txt"
    params:
        min_quality = 20
    threads: 4
    resources:
        mem_mb = 8000,
        disk_mb = 50000
    log:
        "logs/{sample}.log"
    benchmark:
        "benchmarks/{sample}.tsv"
    conda:
        "envs/tool.yaml"
    shell:
        """
        some_tool \
            --threads {threads} \
            --min-quality {params.min_quality} \
            --input {input} \
            --output {output} \
            2> {log}
        """
```

### 4.2 Wildcards

Wildcards are placeholders in file paths enclosed in curly braces. Snakemake infers wildcard values by matching requested output files against rule output patterns.

```python
rule trim:
    input:
        "data/fastq/{sample}_{read}.fastq.gz"
    output:
        "results/trimmed/{sample}_{read}.trimmed.fastq.gz"
    shell:
        "fastp -i {input} -o {output}"
```

When Snakemake needs `results/trimmed/sampleA_R1.trimmed.fastq.gz`, it resolves `sample=sampleA` and `read=R1`.

**Wildcard constraints** prevent ambiguous matches:

```python
# At the top of the Snakefile (global constraint)
wildcard_constraints:
    sample = "[A-Za-z0-9_]+",
    read = "R[12]"

# Or per-rule
rule trim:
    wildcard_constraints:
        sample = "[^/]+"
    input: ...
    output: ...
```

### 4.3 expand()

`expand()` generates lists of file names by combining wildcards with values. It is typically used in `rule all` to declare all desired final outputs.

```python
SAMPLES = ["wt_rep1", "wt_rep2", "ko_rep1", "ko_rep2"]
READS = ["R1", "R2"]

rule all:
    input:
        # Cartesian product: all samples x all reads
        expand("results/trimmed/{sample}_{read}.trimmed.fastq.gz",
               sample=SAMPLES, read=READS),
        # Zip (parallel lists, not product)
        expand("results/merged/{sample}.bam",
               zip, sample=["merged_wt", "merged_ko"],
               allow_missing=True)
```

**Important**: `expand()` is evaluated at DAG-build time, not at rule execution time. All values must be known before any jobs run (unless you use checkpoints).

### 4.4 Config Files

Store parameters in a YAML config file to separate data from logic.

```yaml
# config/config.yaml
star_index: "/data/genomes/GRCh38/star_index"
genome_fasta: "/data/genomes/GRCh38/genome.fa"
annotation_gtf: "/data/genomes/GRCh38/genes.gtf"

samples:
  - sample_A
  - sample_B
  - sample_C

params:
  star:
    overhang: 100
  fastp:
    min_length: 36
    quality: 20
```

```python
# Snakefile
configfile: "config/config.yaml"

SAMPLES = config["samples"]

rule star_align:
    params:
        overhang = config["params"]["star"]["overhang"]
    ...
```

Override config values from the command line:

```bash
snakemake --cores 8 --config samples='["sample_X"]'
```

Or provide an additional config file:

```bash
snakemake --cores 8 --configfile config/override.yaml
```

### 4.5 Conda Integration

Define per-rule conda environments so each tool gets its exact required versions:

```yaml
# workflow/envs/star.yaml
name: star
channels:
  - bioconda
  - conda-forge
  - defaults
dependencies:
  - star=2.7.11b
  - samtools=1.20
```

```python
rule star_align:
    conda:
        "envs/star.yaml"
    ...
```

Run with `--use-conda`:

```bash
snakemake --cores 8 --use-conda
```

Snakemake creates and caches the environment automatically. Environments are stored in `.snakemake/conda/` by default.

To pre-create all environments without running the pipeline:

```bash
snakemake --cores 1 --use-conda --conda-create-envs-only
```

### 4.6 Cluster Execution (Slurm)

#### Modern approach: Snakemake executor plugins (Snakemake 8+)

```bash
pip install snakemake-executor-plugin-slurm

snakemake --executor slurm \
    --default-resources slurm_partition=medium mem_mb=8000 runtime=120 \
    --jobs 50 \
    --use-conda
```

Set per-rule resources:

```python
rule star_align:
    threads: 8
    resources:
        mem_mb = 32000,
        runtime = 240,         # minutes
        slurm_partition = "long",
        slurm_extra = "'--gres=tmpdir:100G'"
    ...
```

#### Classic approach: --cluster flag (Snakemake 7 and below)

```bash
snakemake --cluster "sbatch -p medium -t {resources.runtime} \
    --mem={resources.mem_mb} -c {threads} -o logs/slurm/%j.out" \
    --jobs 50 \
    --use-conda
```

#### Profiles

Create a profile to avoid retyping cluster arguments. Place a `config.yaml` in a profile directory:

```yaml
# ~/.config/snakemake/slurm/config.yaml (Snakemake 7)
# or profiles/slurm/config.yaml (Snakemake 8+)
executor: slurm
default-resources:
  slurm_partition: medium
  mem_mb: 8000
  runtime: 120
jobs: 100
use-conda: true
latency-wait: 60
```

```bash
snakemake --profile slurm
# or
snakemake --workflow-profile profiles/slurm
```

### 4.7 Modular Workflows

#### include

`include` injects rules from another `.smk` file into the current namespace:

```python
# Snakefile
configfile: "config/config.yaml"

include: "workflow/rules/trimming.smk"
include: "workflow/rules/mapping.smk"
include: "workflow/rules/quantification.smk"

rule all:
    input:
        expand("results/counts/{sample}.counts.tsv", sample=config["samples"])
```

All included files share the same config, global wildcards, and namespace.

#### module

`module` imports an external workflow (e.g., from GitHub or another directory) and allows renaming, reconfiguring, or overriding outputs:

```python
module mapping_workflow:
    snakefile:
        github("username/mapping-pipeline", path="workflow/Snakefile", tag="v1.2.0")
    config:
        config

use rule * from mapping_workflow as mapping_*
```

### 4.8 Checkpoints

Checkpoints are rules whose output determines downstream wildcard values at runtime. Use them when the number or names of output files are not known until a rule finishes (e.g., splitting a file into an unknown number of chunks, or reading a sample sheet that a previous step generates).

```python
checkpoint split_fastq:
    input:
        "data/{sample}.fastq.gz"
    output:
        directory("results/split/{sample}")
    shell:
        """
        mkdir -p {output}
        split_fastq --input {input} --outdir {output} --chunks auto
        """

def aggregate_split(wildcards):
    """Collect all chunk files produced by the checkpoint."""
    checkpoint_output = checkpoints.split_fastq.get(**wildcards).output[0]
    chunks = glob_wildcards(os.path.join(checkpoint_output, "{chunk}.fastq.gz")).chunk
    return expand("results/aligned/{sample}/{chunk}.bam",
                  sample=wildcards.sample, chunk=chunks)

rule merge_bams:
    input:
        aggregate_split
    output:
        "results/merged/{sample}.bam"
    shell:
        "samtools merge {output} {input}"
```

When Snakemake encounters the checkpoint, it executes it first, then re-evaluates the DAG with the now-known outputs.

### 4.9 temp(), protected(), and directory()

```python
rule align:
    output:
        bam = temp("results/tmp/{sample}.unsorted.bam"),   # deleted after all consuming rules finish
        sorted = protected("results/bam/{sample}.sorted.bam")  # set read-only after creation
    ...

checkpoint split:
    output:
        directory("results/split/{sample}")  # declares output as a directory
    ...
```

- **temp()**: Automatically deletes the file once no downstream rule needs it. Essential for large intermediate BAM/FASTQ files.
- **protected()**: Makes the file read-only after creation to prevent accidental deletion. Use for expensive-to-reproduce outputs.
- **directory()**: Marks the output as a directory rather than a file.

### 4.10 params

`params` holds values that are not file paths. They can be strings, numbers, or even callables (functions that receive `wildcards`, `input`, `output`, `threads`, and `resources`).

```python
rule feature_counts:
    input:
        bam = "results/bam/{sample}.sorted.bam",
        gtf = config["annotation_gtf"]
    output:
        "results/counts/{sample}.counts.tsv"
    params:
        strand = lambda wildcards: get_strandedness(wildcards.sample),
        extra = "-p --countReadPairs -B -C"
    threads: 4
    shell:
        """
        featureCounts \
            -T {threads} \
            -s {params.strand} \
            {params.extra} \
            -a {input.gtf} \
            -o {output} \
            {input.bam}
        """
```

### 4.11 Log Files

Log files capture stderr/stdout. They are NOT automatically deleted when a rule fails (unlike output files), making them invaluable for debugging.

```python
rule trim:
    input:
        r1 = "data/fastq/{sample}_R1.fastq.gz",
        r2 = "data/fastq/{sample}_R2.fastq.gz"
    output:
        r1 = "results/trimmed/{sample}_R1.trimmed.fastq.gz",
        r2 = "results/trimmed/{sample}_R2.trimmed.fastq.gz",
        json = "results/trimmed/{sample}.fastp.json",
        html = "results/trimmed/{sample}.fastp.html"
    log:
        "logs/fastp/{sample}.log"
    shell:
        """
        fastp \
            -i {input.r1} -I {input.r2} \
            -o {output.r1} -O {output.r2} \
            --json {output.json} --html {output.html} \
            2> {log}
        """
```

Always redirect stderr to `{log}` with `2> {log}` or `&> {log}` (for both stdout and stderr).

### 4.12 Benchmarks

The `benchmark` directive records wall clock time, CPU time, max RSS memory, and I/O statistics to a TSV file.

```python
rule star_align:
    benchmark:
        "benchmarks/star/{sample}.tsv"
    ...
```

To run a rule multiple times for benchmarking:

```python
    benchmark:
        repeat("benchmarks/star/{sample}.tsv", 3)
```

The resulting TSV has columns: `s`, `h:m:s`, `max_rss`, `max_vms`, `max_uss`, `max_pss`, `io_in`, `io_out`, `mean_load`, `cpu_time`.

## 5. Common Bioinformatics Patterns

### 5.1 FASTQ to BAM to BigWig Pipeline

A complete RNA-seq processing pipeline:

```python
# config/config.yaml
# star_index: /data/genomes/GRCh38/star_index
# chrom_sizes: /data/genomes/GRCh38/chrom.sizes
# samples: [wt_rep1, wt_rep2, ko_rep1, ko_rep2]

configfile: "config/config.yaml"
SAMPLES = config["samples"]

rule all:
    input:
        expand("results/bigwig/{sample}.bw", sample=SAMPLES),
        "results/qc/multiqc_report.html"

rule fastp_trim:
    input:
        r1 = "data/fastq/{sample}_R1.fastq.gz",
        r2 = "data/fastq/{sample}_R2.fastq.gz"
    output:
        r1 = temp("results/trimmed/{sample}_R1.trimmed.fastq.gz"),
        r2 = temp("results/trimmed/{sample}_R2.trimmed.fastq.gz"),
        json = "results/qc/fastp/{sample}.fastp.json",
        html = "results/qc/fastp/{sample}.fastp.html"
    threads: 4
    log:
        "logs/fastp/{sample}.log"
    conda:
        "envs/fastp.yaml"
    shell:
        """
        fastp \
            -i {input.r1} -I {input.r2} \
            -o {output.r1} -O {output.r2} \
            --json {output.json} --html {output.html} \
            -w {threads} \
            2> {log}
        """

rule star_align:
    input:
        r1 = "results/trimmed/{sample}_R1.trimmed.fastq.gz",
        r2 = "results/trimmed/{sample}_R2.trimmed.fastq.gz",
        index = config["star_index"]
    output:
        bam = temp("results/star/{sample}.Aligned.sortedByCoord.out.bam"),
        log_final = "results/star/{sample}.Log.final.out"
    params:
        out_prefix = "results/star/{sample}."
    threads: 8
    resources:
        mem_mb = 36000
    log:
        "logs/star/{sample}.log"
    benchmark:
        "benchmarks/star/{sample}.tsv"
    conda:
        "envs/star.yaml"
    shell:
        """
        STAR \
            --runThreadN {threads} \
            --genomeDir {input.index} \
            --readFilesIn {input.r1} {input.r2} \
            --readFilesCommand zcat \
            --outSAMtype BAM SortedByCoordinate \
            --outFileNamePrefix {params.out_prefix} \
            --limitBAMsortRAM {resources.mem_mb}000000 \
            2> {log}
        """

rule index_bam:
    input:
        "results/star/{sample}.Aligned.sortedByCoord.out.bam"
    output:
        bam = protected("results/bam/{sample}.sorted.bam"),
        bai = protected("results/bam/{sample}.sorted.bam.bai")
    threads: 4
    log:
        "logs/samtools/{sample}.index.log"
    conda:
        "envs/samtools.yaml"
    shell:
        """
        cp {input} {output.bam} 2> {log}
        samtools index -@ {threads} {output.bam} 2>> {log}
        """

rule bam_to_bigwig:
    input:
        bam = "results/bam/{sample}.sorted.bam",
        bai = "results/bam/{sample}.sorted.bam.bai"
    output:
        "results/bigwig/{sample}.bw"
    threads: 4
    resources:
        mem_mb = 16000
    log:
        "logs/bamCoverage/{sample}.log"
    conda:
        "envs/deeptools.yaml"
    shell:
        """
        bamCoverage \
            --bam {input.bam} \
            --outFileName {output} \
            --binSize 10 \
            --normalizeUsing RPKM \
            --numberOfProcessors {threads} \
            2> {log}
        """

rule multiqc:
    input:
        expand("results/qc/fastp/{sample}.fastp.json", sample=SAMPLES),
        expand("results/star/{sample}.Log.final.out", sample=SAMPLES)
    output:
        "results/qc/multiqc_report.html"
    params:
        outdir = "results/qc"
    log:
        "logs/multiqc.log"
    conda:
        "envs/multiqc.yaml"
    shell:
        """
        multiqc {params.outdir} -o {params.outdir} --force 2> {log}
        """
```

### 5.2 Sample Sheet Driven Workflows

Use a TSV/CSV sample sheet to define sample metadata, rather than listing samples in the config. This is especially useful when samples have different properties (single-end vs. paired-end, different lanes, etc.).

```
# samples.tsv
sample	condition	fq1	fq2
wt_rep1	wildtype	data/fastq/wt_rep1_R1.fastq.gz	data/fastq/wt_rep1_R2.fastq.gz
wt_rep2	wildtype	data/fastq/wt_rep2_R1.fastq.gz	data/fastq/wt_rep2_R2.fastq.gz
ko_rep1	knockout	data/fastq/ko_rep1_R1.fastq.gz	data/fastq/ko_rep1_R2.fastq.gz
ko_rep2	knockout	data/fastq/ko_rep2_R1.fastq.gz	data/fastq/ko_rep2_R2.fastq.gz
```

```python
import pandas as pd

samples_df = pd.read_csv("samples.tsv", sep="\t").set_index("sample", drop=False)

def get_fastq(wildcards):
    """Return FASTQ paths for a given sample from the sample sheet."""
    row = samples_df.loc[wildcards.sample]
    return {"r1": row["fq1"], "r2": row["fq2"]}

SAMPLES = samples_df["sample"].tolist()

rule all:
    input:
        expand("results/bam/{sample}.sorted.bam", sample=SAMPLES)

rule star_align:
    input:
        unpack(get_fastq),
        index = config["star_index"]
    output:
        bam = "results/bam/{sample}.sorted.bam"
    ...
```

The `unpack()` function unpacks dictionary keys into named inputs (`input.r1`, `input.r2`).

#### Multi-lane samples

When a sample is spread across multiple sequencing lanes:

```
# samples.tsv
sample	lane	fq1	fq2
wt_rep1	L001	data/fastq/wt_rep1_L001_R1.fastq.gz	data/fastq/wt_rep1_L001_R2.fastq.gz
wt_rep1	L002	data/fastq/wt_rep1_L002_R1.fastq.gz	data/fastq/wt_rep1_L002_R2.fastq.gz
```

```python
def get_lanes_for_sample(wildcards):
    """Return all lane-level BAMs for merging."""
    rows = samples_df.loc[samples_df["sample"] == wildcards.sample]
    return expand("results/per_lane/{sample}_{lane}.bam",
                  sample=wildcards.sample,
                  lane=rows["lane"].tolist())

rule merge_lanes:
    input:
        get_lanes_for_sample
    output:
        "results/bam/{sample}.merged.bam"
    shell:
        "samtools merge {output} {input}"
```

### 5.3 Scatter-Gather Pattern

Split a large file into chunks, process in parallel, then merge. This is common for variant calling (scatter across chromosomes), large FASTQ processing, or any embarrassingly parallel operation.

```python
CHROMS = [f"chr{i}" for i in range(1, 23)] + ["chrX", "chrY"]

rule all:
    input:
        "results/variants/all_samples.vcf.gz"

rule call_variants_per_chrom:
    input:
        bam = "results/bam/{sample}.sorted.bam",
        bai = "results/bam/{sample}.sorted.bam.bai",
        ref = config["genome_fasta"]
    output:
        vcf = temp("results/variants/{sample}.{chrom}.vcf.gz")
    params:
        region = "{chrom}"
    shell:
        """
        bcftools mpileup -r {params.region} -f {input.ref} {input.bam} | \
        bcftools call -mv -Oz -o {output.vcf}
        """

rule gather_chroms:
    input:
        vcfs = expand("results/variants/{{sample}}.{chrom}.vcf.gz", chrom=CHROMS)
    output:
        "results/variants/{sample}.vcf.gz"
    shell:
        "bcftools concat {input.vcfs} -Oz -o {output}"
```

Note the double braces `{{sample}}` inside `expand()` -- this keeps `sample` as a wildcard while expanding only `chrom`.

#### Using scattergather (built-in)

Snakemake provides a built-in scatter-gather mechanism:

```python
scattergather:
    split = 8

rule scatter_input:
    input:
        "data/{sample}.fastq.gz"
    output:
        scatter.split("results/split/{{sample}}.{scatteritem}.fastq.gz")
    ...

rule process_chunk:
    input:
        "results/split/{sample}.{scatteritem}.fastq.gz"
    output:
        "results/processed/{sample}.{scatteritem}.txt"
    ...

rule gather_output:
    input:
        gather.split("results/processed/{{sample}}.{scatteritem}.txt")
    output:
        "results/final/{sample}.txt"
    ...
```

## 6. Key Concepts

### 6.1 DAG Resolution

Snakemake works backwards from the target files (specified in `rule all` or on the command line):

1. It starts with the requested output files.
2. For each file, it finds which rule can produce it by matching output patterns.
3. It determines the input files for that rule, then recursively finds rules to produce those inputs.
4. This continues until it reaches files that already exist (base case).
5. The result is a DAG where nodes are jobs and edges are file dependencies.

Only jobs whose outputs are missing or older than their inputs are scheduled for execution.

Inspect the DAG:

```bash
# Full DAG (can be large)
snakemake --dag | dot -Tsvg > dag.svg

# Simplified rule-level graph
snakemake --rulegraph | dot -Tsvg > rulegraph.svg

# File-level graph
snakemake --filegraph | dot -Tsvg > filegraph.svg
```

### 6.2 Wildcard Constraints

Wildcard constraints restrict what strings a wildcard can match. Without constraints, a wildcard matches any non-empty string (except `/`), which can cause ambiguous rule matching.

```python
# Global constraints (apply to all rules)
wildcard_constraints:
    sample = "[A-Za-z0-9_-]+",
    chrom = "chr[0-9XY]+",
    read = "R[12]"

# Per-rule constraint
rule align:
    wildcard_constraints:
        sample = "(?!merged).*"  # exclude "merged" as a sample name
    output:
        "results/bam/{sample}.bam"
    ...
```

Common patterns:

- `[^/]+` -- match anything except path separators (default behavior).
- `\d+` -- digits only.
- `[A-Za-z0-9_-]+` -- alphanumeric plus underscore and hyphen.
- Use negative lookahead `(?!pattern)` to exclude specific strings.

### 6.3 Rule Ordering and Ambiguity

When multiple rules can produce the same output file, Snakemake raises an `AmbiguousRuleException`. Resolve this by:

1. **Wildcard constraints** (preferred): Make patterns non-overlapping.

```python
rule align_single:
    wildcard_constraints:
        sample = "SE_.*"
    output:
        "results/bam/{sample}.bam"

rule align_paired:
    wildcard_constraints:
        sample = "PE_.*"
    output:
        "results/bam/{sample}.bam"
```

2. **ruleorder**: Declare explicit priority.

```python
ruleorder: specific_rule > general_rule
```

3. **Rule priority**: Assign numeric priority (higher wins).

```python
rule special_case:
    priority: 50
    output: "results/{sample}.txt"
    ...
```

## 7. Common Pitfalls

### Outputs not created exactly as declared

Snakemake checks that every declared output file exists after a rule finishes. If the actual file path differs from the declared output (even by a trailing slash or different extension), the rule fails. Always verify that the command actually writes to the exact path in `output`.

### Using shell variables without escaping

In `shell` blocks, curly braces are interpreted by Snakemake. To use shell variables, double the braces:

```python
# WRONG -- Snakemake will try to resolve {line}
shell:
    "while read line; do echo {line}; done < {input}"

# CORRECT -- double braces escape to literal shell braces
shell:
    "while read line; do echo ${{line}}; done < {input}"
```

### Forgetting --use-conda

If a rule specifies `conda:` but you do not pass `--use-conda` on the command line, the conda environment is silently ignored and the rule runs in the base environment. This often causes "command not found" errors.

### Wildcards in expand() vs. rule patterns

A common mistake is confusing `expand()` (which produces concrete file lists at parse time) with rule wildcards (which are resolved at DAG time). Inside `expand()`, use `{{wildcard}}` (double braces) to keep a wildcard unresolved:

```python
# WRONG: tries to resolve sample immediately, fails
expand("results/{sample}.{chrom}.vcf", sample=SAMPLES, chrom=CHROMS)

# When you want chrom expanded but sample kept as wildcard:
expand("results/{{sample}}.{chrom}.vcf", chrom=CHROMS)
```

### Not using temp() for large intermediates

Genomic pipelines generate massive intermediate files (unsorted BAMs, uncompressed FASTQs). Forgetting `temp()` can fill up disk. Mark all intermediate files that downstream rules consume as `temp()`.

### Race conditions with shared output directories

If multiple rules write to the same directory simultaneously, files can collide. Give each rule its own output directory or use `directory()` properly.

### Log file directory not existing

Snakemake creates output file directories automatically but does NOT auto-create log file directories. Either create them in the shell block or ensure they exist:

```python
rule example:
    log:
        "logs/step/{sample}.log"
    shell:
        """
        mkdir -p $(dirname {log})
        some_command 2> {log}
        """
```

Alternatively, in Snakemake 8+ you can use the `--directory` flag or ensure the log directory exists via a common setup rule.

### Modifying input files in place

Rules should never modify their input files. Snakemake uses file timestamps to determine what is up to date. If a rule modifies an input, it can trigger an infinite re-execution loop or corrupt upstream outputs.

### Forgetting the --latency-wait flag on clusters

On shared filesystems (NFS, Lustre), there can be a delay before newly created files are visible. Use `--latency-wait 60` (seconds) to give the filesystem time to sync:

```bash
snakemake --executor slurm --latency-wait 60 ...
```

### Thread oversubscription

The `threads` directive tells Snakemake how many cores a job needs for scheduling purposes, but it does not enforce a CPU limit. If a tool internally uses more threads than declared, you can overload the machine. Always pass `{threads}` to the tool's thread/core argument.

### Using run blocks with conda

The `run:` directive executes Python code in the main Snakemake process. It does NOT run inside the conda environment specified by `conda:`. If you need conda-managed packages in Python code, use `script:` instead:

```python
# WRONG: pandas from conda env not available in run block
rule process:
    conda: "envs/pandas.yaml"
    run:
        import pandas as pd  # uses main env, not conda env
        ...

# CORRECT: use script directive
rule process:
    conda: "envs/pandas.yaml"
    script:
        "scripts/process.py"
```

In the script file, access Snakemake objects via `snakemake.input`, `snakemake.output`, `snakemake.params`, etc.
