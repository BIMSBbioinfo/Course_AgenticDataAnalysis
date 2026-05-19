---
name: slurm-hpc
description: Slurm HPC job management. Submit batch and array jobs, manage queues and partitions, monitor job status, configure resource requests (memory, CPUs, GPUs), and design efficient job arrays for genomics workloads.
license: MIT license
metadata:
    skill-author: VFranke
---

# Slurm HPC Job Management for Genomics

## Overview

This skill provides guidance for submitting, managing, and optimizing jobs on Slurm-managed HPC clusters. It covers batch job submission, job arrays for sample-parallel processing, resource estimation, job monitoring, and dependency chains. The focus is on genomics and bioinformatics workloads: RNA-seq alignment, variant calling, single-cell processing, and pipeline orchestration with Snakemake.

All examples assume a standard Slurm installation. Cluster-specific details (partition names, resource limits, module systems) vary by site. Use `sinfo` and `sacctmgr show qos` to discover your cluster's configuration.

## When to Use

Use this skill when the user needs to:

- **Submit batch jobs** to a Slurm cluster with appropriate resource requests
- **Design job arrays** for sample-parallel genomics processing
- **Estimate and tune resources** (memory, CPUs, wall time) for bioinformatics tools
- **Monitor running jobs** and diagnose failures (OOM kills, timeouts)
- **Build dependency chains** between pipeline stages
- **Run interactive sessions** for debugging or exploratory analysis
- **Integrate Snakemake** with Slurm for automated pipeline execution
- **Optimize I/O** using local scratch for alignment and sorting steps

## Quick Start

### Submit a batch job

```bash
sbatch my_script.sh
```

### Check your queued and running jobs

```bash
squeue -u $USER
```

### Cancel a job

```bash
scancel 12345          # cancel by job ID
scancel -u $USER       # cancel all your jobs
scancel -n my_job      # cancel by job name
```

### Minimal batch script

```bash
#!/bin/bash
#SBATCH --job-name=align_sample
#SBATCH --mem=32G
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

module load star/2.7.11b
STAR --runThreadN $SLURM_CPUS_PER_TASK \
     --genomeDir /data/references/star_index \
     --readFilesIn sample_R1.fastq.gz sample_R2.fastq.gz \
     --readFilesCommand zcat \
     --outSAMtype BAM SortedByCoordinate
```

## Core Capabilities

### sbatch Directives

Place `#SBATCH` directives at the top of your submission script, before any executable commands. These are the most commonly used directives for genomics work:

```bash
#!/bin/bash
#SBATCH --job-name=rnaseq_align       # short descriptive name (shows in squeue)
#SBATCH --mem=32G                      # total memory for the job
#SBATCH --cpus-per-task=8              # number of CPU cores
#SBATCH --time=08:00:00               # wall time limit (HH:MM:SS)
#SBATCH --partition=medium             # partition (queue) to submit to
#SBATCH --output=logs/%x_%j.out       # stdout file (%x=job name, %j=job ID)
#SBATCH --error=logs/%x_%j.err        # stderr file
#SBATCH --mail-type=END,FAIL          # send email on completion or failure
#SBATCH --mail-user=user@example.com  # email address for notifications
```

**Key directive reference:**

| Directive             | Purpose                                 | Example                          |
|-----------------------|-----------------------------------------|----------------------------------|
| `--mem`               | Total memory per node                   | `--mem=32G`                      |
| `--mem-per-cpu`       | Memory per allocated CPU core           | `--mem-per-cpu=4G`               |
| `--cpus-per-task`     | CPU cores for a single task             | `--cpus-per-task=8`              |
| `--time`              | Maximum wall time                       | `--time=12:00:00`                |
| `--partition`         | Target partition                        | `--partition=long`               |
| `--output`            | Stdout log path                         | `--output=logs/%x_%j.out`       |
| `--error`             | Stderr log path                         | `--error=logs/%x_%j.err`        |
| `--job-name`          | Job name for identification             | `--job-name=star_align`          |
| `--mail-type`         | When to send email notifications        | `--mail-type=END,FAIL`           |
| `--mail-user`         | Email recipient                         | `--mail-user=user@example.com`   |
| `--gres`              | Generic resources (e.g., GPUs)          | `--gres=gpu:1`                   |
| `--ntasks`            | Number of tasks (for MPI)               | `--ntasks=1`                     |
| `--nodes`             | Number of nodes                         | `--nodes=1`                      |
| `--qos`               | Quality of service                      | `--qos=high`                     |
| `--account`           | Billing account                         | `--account=proj_rnaseq`          |

**Log file patterns:**

- `%j` -- job ID
- `%x` -- job name
- `%a` -- array task ID
- `%A` -- array master job ID

Always create the `logs/` directory before submitting: `mkdir -p logs`.

### Job Arrays

Job arrays are the primary mechanism for sample-parallel processing in genomics. A single `sbatch` submission creates many independent tasks, each identified by `$SLURM_ARRAY_TASK_ID`.

#### Basic array submission

```bash
#!/bin/bash
#SBATCH --job-name=align
#SBATCH --array=1-100
#SBATCH --mem=32G
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err

# Each task gets a unique SLURM_ARRAY_TASK_ID from 1 to 100
echo "Processing array task: $SLURM_ARRAY_TASK_ID"
```

#### Throttling concurrent tasks

Limit how many array tasks run simultaneously to avoid overwhelming shared resources (filesystems, license servers):

```bash
#SBATCH --array=1-100%10    # run at most 10 tasks concurrently
```

#### Reading sample names from a file

This is the standard pattern for genomics array jobs. Create a file listing one sample per line, then index into it using the array task ID:

```bash
#!/bin/bash
#SBATCH --job-name=align
#SBATCH --array=1-48
#SBATCH --mem=32G
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err

# samples.txt contains one sample name per line
SAMPLE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" samples.txt)

echo "Processing sample: $SAMPLE"

module load star/2.7.11b
STAR --runThreadN $SLURM_CPUS_PER_TASK \
     --genomeDir /data/references/star_index \
     --readFilesIn fastq/${SAMPLE}_R1.fastq.gz fastq/${SAMPLE}_R2.fastq.gz \
     --readFilesCommand zcat \
     --outFileNamePrefix aligned/${SAMPLE}_ \
     --outSAMtype BAM SortedByCoordinate
```

Generate the samples file and count lines to set the array range:

```bash
ls fastq/*_R1.fastq.gz | sed 's|fastq/||; s|_R1.fastq.gz||' > samples.txt
wc -l samples.txt   # use this number as the array upper bound
```

#### Array with step size

```bash
#SBATCH --array=0-900:100   # values: 0, 100, 200, ..., 900
```

#### Resubmitting specific failed tasks

```bash
#SBATCH --array=3,17,42     # rerun only tasks 3, 17, and 42
```

### Interactive Jobs

Use `srun` to get an interactive shell on a compute node for debugging, testing commands, or running interactive R/Python sessions:

```bash
# Basic interactive session
srun --pty --mem=8G --cpus-per-task=4 --time=02:00:00 bash

# Interactive session on a specific partition
srun --pty --partition=interactive --mem=16G --time=04:00:00 bash

# Interactive session with a GPU
srun --pty --gres=gpu:1 --mem=32G --time=01:00:00 bash

# Interactive R session
srun --pty --mem=16G --cpus-per-task=4 --time=02:00:00 R
```

Alternatively, use `salloc` to allocate resources and then `ssh` to the allocated node:

```bash
salloc --mem=16G --cpus-per-task=4 --time=02:00:00
# Note the allocated node name, then:
ssh <nodename>
```

### Job Monitoring

#### squeue -- view queued and running jobs

```bash
# Your jobs
squeue -u $USER

# Detailed format
squeue -u $USER -o "%.10i %.20j %.8T %.10M %.6D %.4C %.10m %R"

# Filter by partition
squeue -u $USER -p long

# Show only running jobs
squeue -u $USER -t RUNNING

# Show estimated start time for pending jobs
squeue -u $USER -t PENDING --start
```

**Job state codes:**

| Code | State    | Meaning                                    |
|------|----------|--------------------------------------------|
| PD   | PENDING  | Waiting for resources                      |
| R    | RUNNING  | Currently executing                        |
| CG   | COMPLETING | Finishing up (epilog running)            |
| CD   | COMPLETED | Finished successfully (exit code 0)       |
| F    | FAILED   | Finished with non-zero exit code           |
| TO   | TIMEOUT  | Hit wall time limit                        |
| OOM  | OUT_OF_MEMORY | Killed by OOM                         |
| CA   | CANCELLED | Cancelled by user or admin                |

#### sacct -- historical job accounting

```bash
# Recent jobs with resource usage
sacct --format=JobID,JobName,Partition,State,Elapsed,MaxRSS,MaxVMSize,NCPUS,TotalCPU \
      --starttime=$(date -d '7 days ago' +%Y-%m-%d)

# Specific job details
sacct -j 12345 --format=JobID,JobName,State,Elapsed,MaxRSS,MaxVMSize,NCPUS

# Array job details (shows each task)
sacct -j 12345 --format=JobID%20,JobName,State,Elapsed,MaxRSS

# Completed jobs with exit codes
sacct --format=JobID,JobName,State,ExitCode,Elapsed --state=FAILED \
      --starttime=$(date -d '24 hours ago' +%Y-%m-%d)
```

**Useful sacct format fields:**

| Field       | Description                              |
|-------------|------------------------------------------|
| MaxRSS      | Peak resident memory (actual usage)      |
| MaxVMSize   | Peak virtual memory                      |
| Elapsed     | Wall clock time                          |
| TotalCPU    | Total CPU time consumed                  |
| NCPUS       | Number of allocated CPUs                 |
| ExitCode    | Exit code (0:0 = success)                |
| State       | Final job state                          |

#### seff -- job efficiency report

`seff` provides a quick summary of resource utilization for a completed job:

```bash
seff 12345
```

Output example:

```
Job ID: 12345
State: COMPLETED (exit code 0)
Cores: 8
CPU Utilized: 05:23:11
CPU Efficiency: 67.27% of 08:00:00 core-walltime
Memory Utilized: 24.3 GB
Memory Efficiency: 75.94% of 32.00 GB
Wall Clock: 01:00:00
```

Use `seff` after jobs complete to calibrate future resource requests. Aim for 70-80% memory efficiency.

### Resource Estimation

#### Strategy for new tools

1. **Start generous**: request 2x what you expect, with moderate wall time.
2. **Run a pilot**: submit 2-3 representative samples.
3. **Check with seff**: look at actual memory and CPU usage.
4. **Adjust and submit the full batch**: scale resources to ~120% of observed peak.

```bash
# Check a completed job
seff 12345

# Detailed resource usage across all tasks in an array
sacct -j 12345 --format=JobID,JobName,MaxRSS,Elapsed,State

# Find the maximum memory across array tasks
sacct -j 12345 --format=MaxRSS --noheader | sort -h | tail -5
```

#### Memory estimation for common bioinformatics tools

| Tool                  | Typical Memory   | Notes                                         |
|-----------------------|------------------|-----------------------------------------------|
| STAR (genome align)   | 32-38 GB         | Dominated by genome index loaded into RAM     |
| STAR (transcriptome)  | 16-20 GB         | Smaller index for transcriptome-only mapping  |
| HISAT2                | 8-10 GB          | More memory-efficient than STAR               |
| samtools sort         | 4-8 GB           | Depends on `-m` per-thread setting            |
| samtools index        | 1-2 GB           | Lightweight                                   |
| samtools merge        | 2-4 GB           | Scales with number of input files             |
| BWA MEM              | 8-12 GB          | For human genome                              |
| featureCounts         | 2-4 GB           | Lightweight counting                          |
| GATK HaplotypeCaller  | 8-16 GB          | Set `-Xmx` JVM heap accordingly               |
| GATK BaseRecalibrator | 8-12 GB          | Java heap + overhead                          |
| Picard MarkDuplicates | 8-16 GB          | Needs sorting buffer; set `MAX_RECORDS_IN_RAM`|
| R session (DESeq2)    | 8-16 GB          | Depends on dataset size                       |
| R session (Seurat)    | 16-64 GB         | Large single-cell objects can be very large   |
| Cell Ranger           | 32-64 GB         | 10x Genomics pipeline, needs substantial RAM  |
| kallisto              | 4-8 GB           | Pseudoalignment, relatively lightweight       |
| Salmon                | 8-12 GB          | Quasi-mapping mode                            |
| minimap2              | 8-16 GB          | Long-read alignment                           |
| deepTools bamCoverage | 4-8 GB           | BigWig generation                             |

### Job Dependencies

Chain pipeline stages so that downstream jobs wait for upstream jobs to complete:

```bash
# Submit alignment job
ALIGN_JOB=$(sbatch --parsable align.sh)

# Submit counting job that starts only after alignment succeeds
COUNT_JOB=$(sbatch --parsable --dependency=afterok:${ALIGN_JOB} count.sh)

# Submit DE analysis after counting succeeds
sbatch --dependency=afterok:${COUNT_JOB} de_analysis.sh
```

**Dependency types:**

| Type            | Meaning                                              |
|-----------------|------------------------------------------------------|
| `afterok:jobid` | Start after jobid completes successfully (exit 0)    |
| `afterany:jobid`| Start after jobid terminates (regardless of status)  |
| `afternotok:jobid` | Start only if jobid fails                         |
| `singleton`     | Only one job with this name runs at a time per user  |

#### Depending on an entire array job

```bash
# Wait for all tasks in array job to succeed
ARRAY_JOB=$(sbatch --parsable --array=1-48 align.sh)
sbatch --dependency=afterok:${ARRAY_JOB} merge_and_count.sh
```

#### Chaining a full pipeline

```bash
#!/bin/bash
# submit_pipeline.sh -- submit a multi-stage genomics pipeline

SAMPLES=48

# Stage 1: Alignment (array job)
JOB1=$(sbatch --parsable --array=1-${SAMPLES}%10 scripts/01_align.sh)
echo "Alignment job: $JOB1"

# Stage 2: Mark duplicates (array job, depends on alignment)
JOB2=$(sbatch --parsable --array=1-${SAMPLES}%10 \
       --dependency=afterok:${JOB1} scripts/02_markdup.sh)
echo "MarkDuplicates job: $JOB2"

# Stage 3: Feature counting (single job after all markdup tasks finish)
JOB3=$(sbatch --parsable --dependency=afterok:${JOB2} scripts/03_count.sh)
echo "Counting job: $JOB3"

# Stage 4: Differential expression (after counting)
JOB4=$(sbatch --parsable --dependency=afterok:${JOB3} scripts/04_de.sh)
echo "DE analysis job: $JOB4"

echo "Pipeline submitted. Final job: $JOB4"
```

### Environment Variables

Slurm sets several environment variables inside running jobs that you should use in your scripts:

| Variable                    | Description                                      |
|-----------------------------|--------------------------------------------------|
| `$SLURM_JOB_ID`            | Unique ID of the current job                     |
| `$SLURM_ARRAY_TASK_ID`     | Index of the current array task                  |
| `$SLURM_ARRAY_JOB_ID`      | Job ID of the array master job                   |
| `$SLURM_CPUS_PER_TASK`     | Number of CPUs allocated to this task            |
| `$SLURM_MEM_PER_NODE`      | Total memory allocated (in MB)                   |
| `$SLURM_JOB_NAME`          | Job name from `--job-name`                       |
| `$SLURM_SUBMIT_DIR`        | Directory where `sbatch` was called              |
| `$SLURM_JOB_NODELIST`      | Node(s) assigned to the job                      |
| `$SLURM_NTASKS`            | Number of tasks                                  |
| `$TMPDIR`                   | Local scratch directory (cluster-specific)       |

**Always use `$SLURM_CPUS_PER_TASK` for thread counts** instead of hardcoding:

```bash
# CORRECT: threads match allocated CPUs
STAR --runThreadN $SLURM_CPUS_PER_TASK ...
samtools sort -@ $SLURM_CPUS_PER_TASK ...

# WRONG: hardcoded thread count may not match allocation
STAR --runThreadN 16 ...
```

### Partition Selection and QOS

#### Viewing available partitions

```bash
# List all partitions with their limits
sinfo -s

# Detailed view: nodes, CPUs, memory, time limits
sinfo -o "%20P %5a %.10l %16F %10m %10G"

# Show partition-specific limits
scontrol show partition <partition_name>
```

#### Choosing the right partition

| Partition type | Typical use                                  | Wall time      |
|----------------|----------------------------------------------|----------------|
| short/quick    | Small tests, samtools index, file checks     | 1-4 hours      |
| medium/normal  | STAR alignment, variant calling              | 12-48 hours    |
| long           | Genome assembly, large R jobs                | 48 hours - 7 days |
| interactive    | Debugging, exploratory R/Python sessions     | 2-8 hours      |
| gpu            | GPU-accelerated tools (basecalling, etc.)    | Varies         |
| highmem        | Jobs needing >256 GB RAM                     | Varies         |

#### Quality of Service (QOS)

QOS policies set additional constraints or priorities on top of partitions:

```bash
# View available QOS
sacctmgr show qos format=Name,MaxWall,MaxTRES,Priority

# Submit with specific QOS
sbatch --qos=high --partition=medium my_script.sh
```

## Bioinformatics Patterns

### Sample-Parallel Processing with Job Arrays

The most common genomics pattern: process each sample independently, then merge results.

```bash
#!/bin/bash
#SBATCH --job-name=rnaseq_align
#SBATCH --array=1-48%10
#SBATCH --mem=35G
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err

set -euo pipefail

# Read sample name from file
SAMPLE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" samples.txt)

echo "=== $(date) === Processing sample: ${SAMPLE} ==="
echo "Job ID: ${SLURM_JOB_ID}, Array Task: ${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname), CPUs: ${SLURM_CPUS_PER_TASK}"

# Load modules
module load star/2.7.11b
module load samtools/1.19

# Create output directory
OUTDIR="aligned/${SAMPLE}"
mkdir -p "$OUTDIR"

# Run alignment
STAR --runThreadN $SLURM_CPUS_PER_TASK \
     --genomeDir /data/references/star_index_hg38 \
     --readFilesIn fastq/${SAMPLE}_R1.fastq.gz fastq/${SAMPLE}_R2.fastq.gz \
     --readFilesCommand zcat \
     --outFileNamePrefix ${OUTDIR}/${SAMPLE}_ \
     --outSAMtype BAM SortedByCoordinate \
     --outSAMattributes NH HI AS NM MD \
     --quantMode GeneCounts

# Index the BAM
samtools index ${OUTDIR}/${SAMPLE}_Aligned.sortedByCoord.out.bam

echo "=== $(date) === Done ==="
```

### Reading Sample Names from a File in Array Jobs

Several approaches for mapping array indices to sample metadata:

#### Simple: one sample per line

```bash
# samples.txt:
# sample_A
# sample_B
# sample_C
SAMPLE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" samples.txt)
```

#### With metadata columns (TSV)

```bash
# sample_sheet.tsv:
# sample_id    condition    fastq_r1                    fastq_r2
# sample_A     treated      fastq/sample_A_R1.fq.gz    fastq/sample_A_R2.fq.gz
# sample_B     control      fastq/sample_B_R1.fq.gz    fastq/sample_B_R2.fq.gz

LINE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" sample_sheet.tsv)
SAMPLE=$(echo "$LINE" | cut -f1)
CONDITION=$(echo "$LINE" | cut -f2)
FASTQ_R1=$(echo "$LINE" | cut -f3)
FASTQ_R2=$(echo "$LINE" | cut -f4)
```

#### Using awk for specific columns

```bash
SAMPLE=$(awk -v idx="$SLURM_ARRAY_TASK_ID" 'NR==idx {print $1}' samples.txt)
```

#### Handling headers

If your sample sheet has a header line, skip it:

```bash
# Add 1 to task ID to skip header
SAMPLE=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" sample_sheet.tsv | cut -f1)
```

Or create the sample list without the header:

```bash
tail -n +2 sample_sheet.tsv | cut -f1 > samples.txt
```

### Using Local Scratch ($TMPDIR) for I/O-Intensive Jobs

Many bioinformatics tools are I/O bound. Writing temporary files to local scratch (`$TMPDIR`) instead of networked filesystems dramatically improves performance and reduces load on shared storage.

```bash
#!/bin/bash
#SBATCH --job-name=sort_bam
#SBATCH --mem=16G
#SBATCH --cpus-per-task=8
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err

set -euo pipefail

SAMPLE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" samples.txt)
INPUT_BAM="aligned/${SAMPLE}.bam"
FINAL_BAM="sorted/${SAMPLE}.sorted.bam"

# Create a working directory on local scratch
SCRATCH="${TMPDIR}/${SLURM_JOB_ID}"
mkdir -p "$SCRATCH"

# Copy input to local scratch
cp "$INPUT_BAM" "$SCRATCH/"

# Sort on local scratch (fast local I/O)
samtools sort \
    -@ $SLURM_CPUS_PER_TASK \
    -m 1G \
    -T "$SCRATCH/tmp" \
    -o "$SCRATCH/${SAMPLE}.sorted.bam" \
    "$SCRATCH/${SAMPLE}.bam"

samtools index "$SCRATCH/${SAMPLE}.sorted.bam"

# Copy results back to shared storage
mkdir -p sorted/
cp "$SCRATCH/${SAMPLE}.sorted.bam" "$FINAL_BAM"
cp "$SCRATCH/${SAMPLE}.sorted.bam.bai" "${FINAL_BAM}.bai"

# Clean up scratch
rm -rf "$SCRATCH"

echo "Done: $FINAL_BAM"
```

**Tools that benefit most from local scratch:**

- `samtools sort` (heavy temp file I/O)
- `STAR` (writes temporary BAM files during sorting)
- `picard MarkDuplicates` (writes sorting spill files)
- `GATK` (temporary files during variant calling)
- Any tool that creates many small intermediate files

### Snakemake --slurm Integration

Snakemake 8+ has built-in Slurm integration via the `--slurm` executor plugin.

#### Basic Snakemake + Slurm

```bash
snakemake --slurm --jobs 50 --default-resources \
    slurm_partition=medium \
    mem_mb=8000 \
    runtime=240 \
    cpus_per_task=1
```

#### Per-rule resources in Snakefile

```python
rule star_align:
    input:
        r1 = "fastq/{sample}_R1.fastq.gz",
        r2 = "fastq/{sample}_R2.fastq.gz",
        index = "/data/references/star_index"
    output:
        bam = "aligned/{sample}/Aligned.sortedByCoord.out.bam"
    threads: 8
    resources:
        mem_mb = 35000,
        runtime = 240,           # minutes
        slurm_partition = "medium"
    shell:
        """
        STAR --runThreadN {threads} \
             --genomeDir {input.index} \
             --readFilesIn {input.r1} {input.r2} \
             --readFilesCommand zcat \
             --outFileNamePrefix aligned/{wildcards.sample}/ \
             --outSAMtype BAM SortedByCoordinate
        """
```

#### Snakemake profile for Slurm

Create `~/.config/snakemake/slurm/config.yaml`:

```yaml
executor: slurm
jobs: 100
default-resources:
  slurm_partition: medium
  mem_mb: 8000
  runtime: 120
  cpus_per_task: 1
latency-wait: 60
```

Then run:

```bash
snakemake --profile slurm --jobs 100
```

#### Snakemake with cluster cancel and status

```bash
snakemake --slurm \
    --jobs 100 \
    --latency-wait 60 \
    --rerun-incomplete \
    --default-resources slurm_partition=medium mem_mb=8000 runtime=240
```

## Key Concepts

### Fair-Share Scheduling

Slurm uses fair-share scheduling to balance resource allocation across users and groups. Your job priority is influenced by:

- **Recent usage**: heavy recent usage lowers your priority relative to others.
- **Account/group allocation**: your group may have a defined share of the cluster.
- **Job age**: pending jobs gain priority the longer they wait.
- **Job size**: very large jobs may be harder to schedule due to fragmentation.

Check your current fair-share standing:

```bash
sshare -u $USER
```

Practical implications:
- Submitting thousands of large jobs at once will lower your fair-share priority.
- Use array throttling (`--array=1-1000%50`) to be a good cluster citizen.
- Request only the resources you need; over-requesting wastes your fair-share credit.

### Backfill Scheduling

Slurm uses backfill to start smaller/shorter jobs while large jobs wait for resources. This means:

- **Accurate wall time estimates help everyone**: if you request 48 hours but your job only runs for 2 hours, the scheduler cannot backfill around it effectively.
- **Shorter jobs may start sooner**: a job requesting 1 hour of wall time can backfill into gaps that a 24-hour job cannot.
- Request realistic wall times with a 20-30% buffer rather than always requesting the partition maximum.

### Resource Limits

Clusters impose limits at multiple levels:

```bash
# View your association limits
sacctmgr show assoc where user=$USER format=Account,Partition,MaxJobs,MaxSubmit,MaxTRES

# View QOS limits
sacctmgr show qos format=Name,MaxWall,MaxTRESPerUser,MaxJobsPerUser,Priority

# View partition limits
scontrol show partition
```

Common limits:
- **MaxJobs**: maximum number of simultaneously running jobs.
- **MaxSubmit**: maximum number of jobs (running + pending) in the queue.
- **MaxTRES**: maximum total resources (e.g., CPU cores, memory, GPUs) across all your running jobs.
- **MaxWall**: maximum wall time per job.

## Common Pitfalls

### 1. Out-of-Memory (OOM) Kills

The most common failure mode for genomics jobs. Slurm kills jobs that exceed their memory allocation.

**Symptoms:**
- Job state shows `OUT_OF_MEMORY` in `sacct`
- Stderr contains `slurmstepd: error: Detected 1 oom-kill` or `Killed`
- Job exits with signal 9 (SIGKILL)

**Diagnosis:**

```bash
# Check if job was OOM-killed
sacct -j 12345 --format=JobID,State,ExitCode,MaxRSS
seff 12345
```

**Solutions:**
- Increase `--mem` by 25-50% above observed peak.
- For Java tools (GATK, Picard), the JVM heap (`-Xmx`) must be less than `--mem` to leave room for JVM overhead. Allocate ~80% to heap: `--mem=16G` with `-Xmx12g`.
- For samtools sort, set `-m` (per-thread memory) so total is within allocation: with 8 threads and `--mem=16G`, use `-m 1500M`.

### 2. Wall Time Too Short

**Symptoms:**
- Job state shows `TIMEOUT` in `sacct`.
- Job terminates abruptly with no error in your log files.

**Solutions:**
- Check elapsed time of past successful runs with `sacct` or `seff`.
- Add a 30% buffer to observed wall times.
- Consider that I/O contention on shared filesystems can make jobs slower during peak hours.
- For long-running tools, consider checkpointing if supported.

### 3. Forgetting --cpus-per-task with Multithreaded Tools

If you request `--cpus-per-task=1` (the default) but your tool uses 8 threads, those threads will compete for a single allocated core, leading to:
- Poor performance (threads contend for CPU)
- Potential issues with other users' jobs on the same node

```bash
# WRONG: requesting 1 CPU but using 8 threads
#SBATCH --mem=32G
# (--cpus-per-task defaults to 1)
STAR --runThreadN 8 ...

# CORRECT: match CPU request to thread count
#SBATCH --mem=32G
#SBATCH --cpus-per-task=8
STAR --runThreadN $SLURM_CPUS_PER_TASK ...
```

### 4. /tmp vs $TMPDIR

`/tmp` is a system directory shared by all users and all jobs on a node. It is often small and not cleaned between jobs. `$TMPDIR` is a Slurm-managed per-job temporary directory on local scratch, cleaned automatically when your job ends.

```bash
# WRONG: using /tmp (shared, may be small, not cleaned)
samtools sort -T /tmp/mysort input.bam -o output.bam

# CORRECT: using $TMPDIR (per-job, local scratch, auto-cleaned)
samtools sort -T $TMPDIR/mysort input.bam -o output.bam

# ALSO CORRECT: explicit subdirectory in $TMPDIR
mkdir -p $TMPDIR/$SLURM_JOB_ID
samtools sort -T $TMPDIR/$SLURM_JOB_ID/mysort input.bam -o output.bam
```

Note: Some clusters do not set `$TMPDIR` automatically. Check your cluster documentation or verify with `echo $TMPDIR` in an interactive job. If `$TMPDIR` is not set, ask your sysadmin about the correct local scratch path (common alternatives: `/scratch/$USER`, `/local/tmp`).

### 5. Not Creating Log Directories Before Submission

Slurm will silently fail to create output/error files if the directory does not exist. The job may run but you lose all log output.

```bash
# ALWAYS create the log directory before submitting
mkdir -p logs
sbatch my_script.sh
```

### 6. Submitting from the Wrong Directory

`#SBATCH --output=logs/%x_%j.out` is relative to the directory where `sbatch` is called (the submit directory). If you `cd` before running `sbatch`, logs end up in unexpected places.

```bash
# Be explicit about paths or always submit from the project root
cd /data/projects/rnaseq
sbatch scripts/align.sh
```

### 7. Not Using set -euo pipefail

Without this, scripts continue running after errors, producing corrupt or incomplete results.

```bash
#!/bin/bash
#SBATCH ...
set -euo pipefail   # exit on error, undefined vars, pipe failures

# Now if STAR fails, the script stops immediately
```

### 8. Overloading Shared Filesystems

Submitting hundreds of jobs that all read from or write to the same network filesystem simultaneously can cause severe I/O contention, slowing down all users.

**Solutions:**
- Throttle array jobs: `--array=1-500%20`
- Use local scratch (`$TMPDIR`) for intermediate files
- Stagger job start times if needed
- Avoid many small file operations; prefer fewer large files

### 9. Ignoring Exit Codes in Dependency Chains

If you use `--dependency=afterok:jobid` but the upstream job fails, the dependent job will never start (state: `DependencyNeverSatisfied`). Monitor your pipeline and use `afterany` if the downstream job should run regardless.

```bash
# Strict: downstream only runs if upstream succeeds
sbatch --dependency=afterok:${JOB1} downstream.sh

# Permissive: downstream runs regardless (useful for cleanup scripts)
sbatch --dependency=afterany:${JOB1} cleanup.sh
```

### 10. Not Checking Job Efficiency After Runs

Wasting resources (requesting 64 GB when you use 8 GB) hurts your fair-share priority and wastes cluster capacity. Always check efficiency for new workloads:

```bash
# After your first batch completes
seff <jobid>

# For array jobs, check several tasks
for taskid in 12345_1 12345_10 12345_25; do
    echo "=== Task $taskid ==="
    seff $taskid
done
```
