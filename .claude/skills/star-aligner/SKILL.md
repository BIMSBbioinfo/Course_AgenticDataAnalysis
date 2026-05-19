---
name: star-aligner
description: STAR RNA-seq aligner. Generate genome indices, align RNA-seq reads with splice-aware mapping, detect chimeric alignments, quantify gene expression, and configure parameters for single-cell and bulk RNA-seq.
license: MIT license
metadata:
    skill-author: VFranke
---

# STAR (Spliced Transcripts Alignment to a Reference)

## Overview

STAR is an ultrafast universal RNA-seq aligner designed for mapping RNA-seq reads to a reference genome. It uses a seed-and-extend strategy with uncompressed suffix arrays for rapid alignment. STAR performs splice-aware alignment, meaning it can map reads that span exon-exon junctions, which is essential for RNA-seq data where mature mRNA transcripts have introns removed.

STAR operates in two main modes: genome index generation and read alignment. It is widely used for bulk RNA-seq, single-cell RNA-seq (via STARsolo), fusion gene detection, and gene expression quantification.

Key properties of STAR:
- Extremely fast alignment speed (can align 100 million 100 bp reads in ~30 minutes)
- High mapping accuracy with splice-aware alignment
- Built-in gene quantification (replacing the need for a separate counting tool like htseq-count)
- Native single-cell RNA-seq support through STARsolo
- Chimeric/fusion transcript detection
- Two-pass alignment mode for improved novel junction discovery

## When to Use STAR

Use STAR when you need to:
- Align RNA-seq reads (bulk or single-cell) to a reference genome
- Detect novel splice junctions
- Quantify gene or transcript expression directly during alignment
- Detect gene fusions or chimeric transcripts
- Perform single-cell RNA-seq preprocessing (10x Chromium, Drop-seq, etc.)
- Generate inputs for downstream tools like RSEM, DESeq2, or featureCounts

STAR is not suitable for:
- DNA-seq alignment (use BWA or Bowtie2 instead)
- Alignment to transcriptome only without a genome (use Salmon or Kallisto for pseudoalignment)
- Very small genomes like bacteria where simpler aligners suffice (though STAR can handle them with adjusted parameters)
- Systems with less than 32 GB of RAM for human-scale genomes

## Quick Start

### Step 1: Generate Genome Index

```bash
STAR \
    --runMode genomeGenerate \
    --genomeDir /path/to/genome_index \
    --genomeFastaFiles /path/to/genome.fa \
    --sjdbGTFfile /path/to/annotations.gtf \
    --sjdbOverhang 99 \
    --runThreadN 8
```

The `--sjdbOverhang` value should ideally be set to read length minus 1. For 100 bp reads, use 99. The default value of 100 works reasonably well for most read lengths.

### Step 2: Align Reads

```bash
STAR \
    --runMode alignReads \
    --genomeDir /path/to/genome_index \
    --readFilesIn sample_R1.fastq.gz sample_R2.fastq.gz \
    --readFilesCommand zcat \
    --outSAMtype BAM SortedByCoordinate \
    --outFileNamePrefix /path/to/output/sample_ \
    --runThreadN 8
```

This produces a coordinate-sorted BAM file ready for downstream analysis.

## Core Capabilities

### Genome Index Generation

The genome index must be generated once per genome/annotation combination and can be reused for all subsequent alignments.

```bash
STAR \
    --runMode genomeGenerate \
    --genomeDir /path/to/genome_index \
    --genomeFastaFiles /path/to/genome.fa \
    --sjdbGTFfile /path/to/annotations.gtf \
    --sjdbOverhang 99 \
    --runThreadN 8
```

Key parameters for genome generation:

| Parameter | Description |
|-----------|-------------|
| `--genomeDir` | Directory where the index will be written (must exist before running) |
| `--genomeFastaFiles` | One or more FASTA files with the genome sequence |
| `--sjdbGTFfile` | GTF annotation file for splice junction database construction |
| `--sjdbOverhang` | Length of the donor/acceptor sequence on each side of junctions; ideally read length - 1 |
| `--genomeSAindexNbases` | Must be scaled down for small genomes: `min(14, log2(GenomeLength)/2 - 1)` |

For small genomes, adjust `--genomeSAindexNbases`:

```bash
# For a small genome like Drosophila (~140 Mb):
STAR --runMode genomeGenerate \
    --genomeSAindexNbases 12 \
    --genomeDir /path/to/dm6_index \
    --genomeFastaFiles dm6.fa \
    --sjdbGTFfile dm6.gtf \
    --sjdbOverhang 99

# For very small genomes (e.g., virus ~10 kb):
STAR --runMode genomeGenerate \
    --genomeSAindexNbases 4 \
    --genomeDir /path/to/virus_index \
    --genomeFastaFiles virus.fa
```

You can also supply a splice junction file directly instead of (or in addition to) a GTF file:

```bash
STAR --runMode genomeGenerate \
    --genomeDir /path/to/genome_index \
    --genomeFastaFiles /path/to/genome.fa \
    --sjdbFileChrStartEnd /path/to/SJ.out.tab \
    --sjdbOverhang 99
```

### Basic Alignment Parameters

```bash
STAR \
    --runMode alignReads \
    --genomeDir /path/to/genome_index \
    --readFilesIn reads_R1.fastq.gz reads_R2.fastq.gz \
    --readFilesCommand zcat \
    --outSAMtype BAM SortedByCoordinate \
    --outFileNamePrefix /output/dir/sample_ \
    --runThreadN 8
```

Key alignment parameters:

| Parameter | Description |
|-----------|-------------|
| `--readFilesIn` | Input read files; for paired-end, give R1 then R2 separated by space |
| `--readFilesCommand` | Command to decompress input files: `zcat` for `.gz`, `bzcat` for `.bz2` |
| `--outSAMtype` | Output format: `BAM SortedByCoordinate`, `BAM Unsorted`, or `SAM` |
| `--outFileNamePrefix` | Prefix for all output files (include trailing `/` or `_`) |
| `--runThreadN` | Number of threads to use |

For multiple input files per mate (e.g., multiple lanes), separate files with commas:

```bash
STAR \
    --readFilesIn lane1_R1.fq.gz,lane2_R1.fq.gz lane1_R2.fq.gz,lane2_R2.fq.gz \
    --readFilesCommand zcat \
    --genomeDir /path/to/genome_index \
    --outSAMtype BAM SortedByCoordinate
```

### Output Options

#### BAM Output Types

```bash
# Coordinate-sorted BAM (ready for visualization and most tools)
--outSAMtype BAM SortedByCoordinate

# Unsorted BAM (faster output, sort later with samtools)
--outSAMtype BAM Unsorted

# Both sorted and unsorted
--outSAMtype BAM SortedByCoordinate Unsorted

# SAM output (uncompressed, large files)
--outSAMtype SAM
```

#### Gene Quantification

```bash
# Gene-level read counts (replaces htseq-count / featureCounts)
--quantMode GeneCounts

# Transcriptome-aligned BAM (input for RSEM)
--quantMode TranscriptomeSAM

# Both gene counts and transcriptome BAM
--quantMode GeneCounts TranscriptomeSAM
```

When using `--quantMode GeneCounts`, STAR produces a `ReadsPerGene.out.tab` file with four columns:
1. Gene ID
2. Unstranded counts
3. Sense-strand counts (for stranded libraries like dUTP, use this column)
4. Antisense-strand counts

For RSEM compatibility with `--quantMode TranscriptomeSAM`, also add:

```bash
--quantMode TranscriptomeSAM GeneCounts \
--outSAMtype BAM SortedByCoordinate \
--quantTranscriptomeBan Singleend
```

#### Signal/Coverage Output

```bash
# bedGraph signal output
--outWigType bedGraph

# Wiggle signal output
--outWigType wiggle

# Strand-specific signal
--outWigStrand Stranded

# Normalize signal
--outWigNorm RPM
```

#### SAM Attributes

```bash
# Standard attributes (recommended for most uses)
--outSAMattributes NH HI AS NM MD

# Include all attributes
--outSAMattributes All

# Minimal attributes for smaller file size
--outSAMattributes Standard
```

### Two-Pass Mapping

Two-pass mapping improves detection of novel splice junctions. In the first pass, STAR identifies junctions. In the second pass, these junctions are used to re-map reads, improving alignment around novel junctions.

```bash
# Automatic two-pass mode (recommended for most use cases)
STAR \
    --genomeDir /path/to/genome_index \
    --readFilesIn reads_R1.fq.gz reads_R2.fq.gz \
    --readFilesCommand zcat \
    --twopassMode Basic \
    --outSAMtype BAM SortedByCoordinate \
    --runThreadN 8
```

With `--twopassMode Basic`, STAR performs both passes automatically in a single run. The first pass discovers novel junctions, and the second pass re-generates the genome index with those junctions included, then re-maps all reads.

For multi-sample projects where you want to share junctions across samples, perform a manual two-pass approach:

```bash
# Pass 1: Run STAR on all samples to collect junctions
for sample in sample1 sample2 sample3; do
    STAR --genomeDir /path/to/genome_index \
         --readFilesIn ${sample}_R1.fq.gz ${sample}_R2.fq.gz \
         --readFilesCommand zcat \
         --outSAMtype None \
         --outFileNamePrefix pass1/${sample}_
done

# Pass 2: Regenerate genome index with all discovered junctions, then align
STAR --runMode genomeGenerate \
     --genomeDir /path/to/genome_index_2pass \
     --genomeFastaFiles /path/to/genome.fa \
     --sjdbGTFfile /path/to/annotations.gtf \
     --sjdbFileChrStartEnd pass1/*_SJ.out.tab \
     --sjdbOverhang 99

for sample in sample1 sample2 sample3; do
    STAR --genomeDir /path/to/genome_index_2pass \
         --readFilesIn ${sample}_R1.fq.gz ${sample}_R2.fq.gz \
         --readFilesCommand zcat \
         --outSAMtype BAM SortedByCoordinate \
         --outFileNamePrefix pass2/${sample}_
done
```

### Chimeric Alignment Detection

Chimeric (fusion) alignments occur when a single read maps to two different genomic locations. This is critical for gene fusion detection in cancer genomics.

```bash
STAR \
    --genomeDir /path/to/genome_index \
    --readFilesIn reads_R1.fq.gz reads_R2.fq.gz \
    --readFilesCommand zcat \
    --outSAMtype BAM SortedByCoordinate \
    --chimSegmentMin 20 \
    --chimOutType Junctions WithinBAM SoftClip \
    --chimJunctionOverhangMin 10 \
    --chimOutJunctionFormat 1 \
    --runThreadN 8
```

Key chimeric alignment parameters:

| Parameter | Description |
|-----------|-------------|
| `--chimSegmentMin` | Minimum mapped length of each chimeric segment; setting to 20 or higher activates chimeric detection |
| `--chimOutType` | Output format: `Junctions` (tabular file), `WithinBAM SoftClip` (chimeric reads in main BAM), `WithinBAM HardClip` |
| `--chimJunctionOverhangMin` | Minimum overhang for chimeric junction |
| `--chimOutJunctionFormat` | Set to 1 for compatible output with STAR-Fusion |
| `--chimMultimapNmax` | Maximum number of multi-alignments for chimeric reads (default 0, increase for sensitivity) |
| `--chimNonchimScoreDropMin` | Minimum score drop for a chimeric alignment to not be considered normal |

For use with STAR-Fusion:

```bash
STAR \
    --genomeDir /path/to/genome_index \
    --readFilesIn reads_R1.fq.gz reads_R2.fq.gz \
    --readFilesCommand zcat \
    --outSAMtype BAM SortedByCoordinate \
    --chimSegmentMin 12 \
    --chimJunctionOverhangMin 8 \
    --chimOutJunctionFormat 1 \
    --alignSJDBoverhangMin 10 \
    --alignMatesGapMax 100000 \
    --alignIntronMax 100000 \
    --alignSJstitchMismatchNmax 5 -1 5 5 \
    --chimMultimapScoreRange 3 \
    --chimScoreJunctionNonGTAG -4 \
    --chimMultimapNmax 20 \
    --chimNonchimScoreDropMin 10 \
    --peOverlapNbasesMin 12 \
    --peOverlapMMp 0.1 \
    --alignInsertionFlush Right \
    --alignSplicedMateMapLminOverLmate 0 \
    --alignSplicedMateMapLmin 30 \
    --chimOutType Junctions WithinBAM SoftClip
```

### STARsolo for Single-Cell RNA-seq

STARsolo is STAR's built-in single-cell RNA-seq pipeline, replacing Cell Ranger for 10x Chromium and supporting other droplet-based protocols.

#### 10x Chromium v3

```bash
STAR \
    --genomeDir /path/to/genome_index \
    --readFilesIn read2.fq.gz read1.fq.gz \
    --readFilesCommand zcat \
    --soloType CB_UMI_Simple \
    --soloCBwhitelist /path/to/3M-february-2018.txt \
    --soloCBstart 1 \
    --soloCBlen 16 \
    --soloUMIstart 17 \
    --soloUMIlen 12 \
    --soloCellFilter EmptyDrops_CR \
    --outSAMtype BAM SortedByCoordinate \
    --outSAMattributes NH HI nM AS CR UR CB UB GX GN sS sQ sM \
    --runThreadN 8
```

Important: For 10x data, Read 2 (cDNA) goes first in `--readFilesIn`, and Read 1 (barcode+UMI) goes second.

#### 10x Chromium v2

```bash
STAR \
    --genomeDir /path/to/genome_index \
    --readFilesIn read2.fq.gz read1.fq.gz \
    --readFilesCommand zcat \
    --soloType CB_UMI_Simple \
    --soloCBwhitelist /path/to/737K-august-2016.txt \
    --soloCBstart 1 \
    --soloCBlen 16 \
    --soloUMIstart 17 \
    --soloUMIlen 10 \
    --soloCellFilter EmptyDrops_CR \
    --outSAMtype BAM SortedByCoordinate \
    --runThreadN 8
```

Note that v2 uses `--soloUMIlen 10` while v3 uses `--soloUMIlen 12`.

#### Key STARsolo Parameters

| Parameter | Description |
|-----------|-------------|
| `--soloType` | Protocol type: `CB_UMI_Simple` for standard droplet protocols (10x, Drop-seq), `CB_UMI_Complex` for more complex barcode structures |
| `--soloCBwhitelist` | Path to barcode whitelist file |
| `--soloUMIlen` | UMI length: 10 for 10x v2, 12 for 10x v3 |
| `--soloCellFilter` | Cell calling method: `EmptyDrops_CR` (Cell Ranger-like), `CellRanger2`, `TopCells`, or `None` |
| `--soloFeatures` | What to quantify: `Gene` (default), `GeneFull` (includes introns for pre-mRNA), `SJ` (splice junctions), `Velocyto` |
| `--soloMultiMappers` | How to handle multi-mapping reads: `Unique`, `EM`, `PropUnique`, `Rescue` |

For pre-mRNA quantification (useful for RNA velocity with scVelo):

```bash
--soloFeatures Gene GeneFull Velocyto
```

### Memory and Performance

#### Thread Control

```bash
# Use 16 threads for alignment
--runThreadN 16

# Limit BAM sorting memory (per thread)
--limitBAMsortRAM 30000000000
```

#### Shared Genome Memory

When running many STAR alignment jobs on the same machine, load the genome into shared memory once to avoid redundant loading:

```bash
# Load genome into shared memory (run once)
STAR --genomeLoad LoadAndKeep --genomeDir /path/to/genome_index

# Run multiple alignment jobs (each reuses loaded genome)
STAR --genomeLoad LoadAndKeep \
     --genomeDir /path/to/genome_index \
     --readFilesIn sample1_R1.fq.gz sample1_R2.fq.gz \
     --readFilesCommand zcat \
     --outSAMtype BAM SortedByCoordinate

# After all jobs are complete, remove genome from shared memory
STAR --genomeLoad Remove --genomeDir /path/to/genome_index
```

Shared memory options:

| Value | Description |
|-------|-------------|
| `NoSharedMemory` | Default; each job loads its own copy of the genome |
| `LoadAndKeep` | Load genome into shared memory and keep it after the run |
| `LoadAndRemove` | Load genome into shared memory and remove after the run |
| `Remove` | Remove genome from shared memory (cleanup) |

#### Memory Estimates

- Human genome index generation: ~32 GB RAM
- Human genome alignment: ~30 GB RAM
- Mouse genome: similar to human (~30 GB)
- Drosophila genome: ~8 GB RAM
- Yeast genome: ~4 GB RAM
- STARsolo adds relatively little overhead on top of standard STAR alignment

### Filtering Parameters

Control which alignments are reported:

```bash
STAR \
    --genomeDir /path/to/genome_index \
    --readFilesIn reads_R1.fq.gz reads_R2.fq.gz \
    --readFilesCommand zcat \
    --outSAMtype BAM SortedByCoordinate \
    --outFilterMultimapNmax 20 \
    --outFilterMismatchNmax 10 \
    --outFilterMismatchNoverReadLmax 0.04 \
    --alignIntronMin 20 \
    --alignIntronMax 1000000 \
    --alignMatesGapMax 1000000 \
    --alignSJoverhangMin 8 \
    --alignSJDBoverhangMin 1 \
    --runThreadN 8
```

Key filtering parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--outFilterMultimapNmax` | 10 | Maximum number of loci a read can map to; reads exceeding this are unmapped |
| `--outFilterMismatchNmax` | 10 | Maximum number of mismatches per read pair |
| `--outFilterMismatchNoverReadLmax` | 1.0 | Maximum ratio of mismatches to read length (set to 0.04 for strict filtering) |
| `--alignIntronMin` | 21 | Minimum intron length |
| `--alignIntronMax` | 0 | Maximum intron length (0 = use default based on genome size) |
| `--alignMatesGapMax` | 0 | Maximum gap between paired-end mates (0 = use default) |
| `--alignSJoverhangMin` | 5 | Minimum overhang for non-annotated splice junctions |
| `--alignSJDBoverhangMin` | 3 | Minimum overhang for annotated splice junctions |
| `--outFilterType` | Normal | Set to `BySJout` to reduce spurious junctions |

To output only uniquely mapped reads:

```bash
--outFilterMultimapNmax 1
```

## Key Concepts

### Splice Junction Database

STAR builds a splice junction database during genome index generation from the GTF annotation file. The `--sjdbOverhang` parameter defines the length of genomic sequence around annotated junctions used in the database. During alignment, STAR uses this database to guide read mapping across known exon-exon junctions while also discovering novel junctions.

The `SJ.out.tab` output file contains all discovered junctions with columns:
1. Chromosome
2. Intron start (1-based)
3. Intron end (1-based)
4. Strand (0 = undefined, 1 = +, 2 = -)
5. Intron motif (0 = non-canonical, 1 = GT/AG, 2 = CT/AC, 3 = GC/AG, 4 = CT/GC, 5 = AT/AC, 6 = GT/AT)
6. Annotated (0 = novel, 1 = annotated)
7. Number of uniquely mapping reads crossing the junction
8. Number of multi-mapping reads crossing the junction
9. Maximum spliced alignment overhang

### Multi-Mapping Reads

Multi-mapping reads (multimappers) are reads that align equally well to multiple genomic locations. STAR reports up to `--outFilterMultimapNmax` alignments per read. By default, one alignment is chosen as primary, and the rest are marked as secondary.

Multi-mapping behavior is controlled by:
- `--outFilterMultimapNmax` -- maximum number of multiple alignments reported
- `--outMultimapperOrder` -- `Old_2.4` (default) or `Random` for random ordering of multimappers
- `--outSAMmultNmax` -- maximum number of alignments written to BAM (-1 = all, default uses outFilterMultimapNmax)

For gene quantification with `--quantMode GeneCounts`, only uniquely mapped reads are counted by default.

### NH and HI BAM Tags

STAR writes several important BAM tags:

| Tag | Description |
|-----|-------------|
| `NH` | Number of reported alignments for this read. NH=1 means uniquely mapped. |
| `HI` | Hit index, indicating which alignment this is (1-based, from 1 to NH) |
| `AS` | Alignment score |
| `NM` | Number of mismatches in the alignment |
| `MD` | String encoding mismatched and deleted reference bases |
| `nM` | Number of mismatches per (paired) alignment |
| `jM` | Intron motifs for all junctions in the alignment |
| `jI` | Intron start and end positions for all junctions |

To filter for uniquely mapped reads from a BAM file, select reads with `NH:i:1`.

## Common Pitfalls

### Memory Requirements for Genome Generation

Human and mouse genome index generation requires approximately 32 GB of RAM. If the machine runs out of memory, STAR will either crash with a segmentation fault or produce a corrupted index. Always ensure sufficient RAM is available before generating an index. For cluster jobs, request at least 35-40 GB to include overhead.

### Setting --sjdbOverhang Correctly

The `--sjdbOverhang` parameter should be set to read length minus 1 for optimal sensitivity. For 150 bp reads, use `--sjdbOverhang 149`. For 100 bp reads, use `--sjdbOverhang 99`. The default value of 100 works reasonably well for most read lengths, but using the ideal value improves mapping of junction-spanning reads. This parameter is set at genome generation time, not at alignment time.

### BAM Sorting Memory

When using `--outSAMtype BAM SortedByCoordinate`, STAR sorts the BAM in memory. For large datasets, this can exceed available RAM and cause crashes. Use `--limitBAMsortRAM` to set an upper limit:

```bash
--limitBAMsortRAM 30000000000   # ~30 GB limit
```

If STAR still runs out of sorting memory, output unsorted BAM and sort with samtools:

```bash
STAR --outSAMtype BAM Unsorted ...
samtools sort -@ 8 -m 4G -o sorted.bam Aligned.out.bam
```

### Genome Directory Must Exist

The directory specified by `--genomeDir` must already exist before running `--runMode genomeGenerate`. STAR will not create it and will fail with an error.

```bash
mkdir -p /path/to/genome_index
```

### Read File Order for Single-Cell Data

For 10x Chromium data with STARsolo, the cDNA read (Read 2) must be specified first in `--readFilesIn`, followed by the barcode/UMI read (Read 1). This is the opposite of many other tools and is a frequent source of errors.

```bash
# Correct order for 10x:
--readFilesIn cDNA_R2.fq.gz barcode_R1.fq.gz

# WRONG (will produce nonsensical results):
--readFilesIn barcode_R1.fq.gz cDNA_R2.fq.gz
```

### Small Genome Index Errors

For small genomes, you must reduce `--genomeSAindexNbases` from its default of 14. The formula is `min(14, log2(GenomeLength)/2 - 1)`. Without this adjustment, STAR will produce a warning and the index may be unnecessarily large or cause errors.

### Temporary Directory Space

STAR creates temporary files in `_STARtmp` within the output directory. For large datasets, especially with two-pass mode, ensure sufficient disk space. You can control the temporary directory location with `--outTmpDir`.

### Running Out of Open File Handles

When using `--outSAMtype BAM SortedByCoordinate` with many threads, STAR may exceed the system limit on open file handles. Increase the limit with `ulimit -n 65535` before running STAR if you encounter "too many open files" errors.

### Compressed Input Requires --readFilesCommand

STAR does not automatically detect compressed input files. If your FASTQ files are gzipped, you must specify `--readFilesCommand zcat`. Omitting this parameter with `.gz` files will cause STAR to fail or produce empty output.
