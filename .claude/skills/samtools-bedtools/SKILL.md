---
name: samtools-bedtools
description: CLI genomics toolkit. Filter, sort, index BAM/CRAM files with samtools, intersect/merge/complement genomic intervals with bedtools, process BAM flags, extract regions, and build shell pipelines for NGS data.
license: MIT license
metadata:
    skill-author: VFranke
---

# samtools-bedtools

Command-line genomics toolkit skill for filtering, manipulating, and analyzing BAM/CRAM alignment files and genomic intervals using samtools and bedtools.

## Overview

This skill provides expertise in building shell commands and pipelines that combine `samtools` and `bedtools` for everyday NGS bioinformatics tasks. It covers BAM/CRAM file manipulation, SAM flag filtering, genomic interval operations, coverage analysis, and multi-tool piping patterns commonly used in production genomics workflows.

## When to use

- Filtering BAM files by alignment flags, regions, read names, or mapping quality
- Converting between BAM, SAM, BED, and other genomic formats
- Intersecting, merging, or complementing genomic intervals
- Computing coverage, depth, and alignment statistics
- Building shell pipelines that chain samtools, bedtools, awk, and grep
- Filtering reads by 10x Genomics barcodes or other BAM tags
- Extracting reads from specific genomic regions
- Preparing files for downstream analysis (sorting, indexing, deduplication)

## Quick start examples

```bash
# Filter to primary alignments only, output BAM
samtools view -b -F 2308 input.bam > primary.bam

# Extract reads from a region
samtools view -b input.bam chr1:1000000-2000000 > region.bam

# Intersect BAM with BED regions
bedtools intersect -abam input.bam -b regions.bed > overlap.bam

# Pipe: extract reverse-strand primary alignments from a region
samtools view -h -F 2308 -f 16 input.bam chr1:1000000-2000000 \
  | samtools view -b - > rev_primary_region.bam

# Filter BAM by 10x barcode
samtools view -h input.bam \
  | awk '$0 ~ /^@/ || $0 ~ /CR:Z:ACGTACGTACGTACGT/' \
  | samtools view -b - > barcode_filtered.bam

# Quick alignment stats
samtools flagstat input.bam
```

## Core capabilities

### SAM flag reference

SAM flags are a bitfield where each bit encodes a property of the alignment. Multiple bits can be set simultaneously. The decimal value is the sum of the individual flag bits.

#### Flag bit values

| Bit | Decimal | Meaning |
|-----|---------|---------|
| 0x1 | 1 | Read is paired |
| 0x2 | 2 | Read mapped in proper pair |
| 0x4 | 4 | Read unmapped |
| 0x8 | 8 | Mate unmapped |
| 0x10 | 16 | Read on reverse strand |
| 0x20 | 32 | Mate on reverse strand |
| 0x40 | 64 | First in pair (read1) |
| 0x80 | 128 | Second in pair (read2) |
| 0x100 | 256 | Secondary alignment |
| 0x200 | 512 | Fails platform/vendor quality checks |
| 0x400 | 1024 | PCR or optical duplicate |
| 0x800 | 2048 | Supplementary alignment |

#### Common flag filter combinations

```bash
# -F excludes reads WITH any of the specified bits set
# -f includes only reads WITH all of the specified bits set

# Mapped reads only (exclude unmapped)
samtools view -F 4 input.bam

# Primary alignments only (exclude unmapped + secondary + supplementary)
# 2308 = 4 + 256 + 2048
samtools view -F 2308 input.bam

# Reverse strand reads only
samtools view -f 16 input.bam

# Forward strand reads only (exclude reverse)
samtools view -F 16 input.bam

# Properly paired reads only
samtools view -f 2 input.bam

# Read1 only from paired-end data
samtools view -f 64 input.bam

# Read2 only from paired-end data
samtools view -f 128 input.bam

# Exclude duplicates
samtools view -F 1024 input.bam

# Primary, non-duplicate, mapped reads
# 3332 = 4 + 256 + 1024 + 2048
samtools view -F 3332 input.bam

# Combine -f and -F: reverse strand primary alignments
samtools view -f 16 -F 2308 input.bam

# Unmapped reads (useful for extracting unaligned reads)
samtools view -f 4 input.bam

# Reads where the mate is unmapped
samtools view -f 8 input.bam
```

#### Decoding flags

```bash
# Decode a flag value to human-readable description
samtools flags 147

# The explain command also works
samtools flags PAIRED,PROPER_PAIR,REVERSE,READ2
```

### BAM filtering patterns

#### Filter by region

```bash
# Single region (requires indexed BAM)
samtools view -b input.bam chr1:1000000-2000000 > region.bam

# Multiple regions
samtools view -b input.bam chr1:1000000-2000000 chr2:5000000-6000000 > regions.bam

# Regions from a BED file
samtools view -b -L regions.bed input.bam > filtered.bam

# Entire chromosome
samtools view -b input.bam chrX > chrX.bam
```

#### Filter by mapping quality

```bash
# Minimum mapping quality of 30
samtools view -b -q 30 input.bam > high_mapq.bam

# Combine with flag filter: primary, high-quality, mapped reads
samtools view -b -F 2308 -q 30 input.bam > high_quality_primary.bam
```

#### Filter by read name

```bash
# Filter by list of read names from a file
samtools view -b -N read_names.txt input.bam > named_reads.bam

# Extract a single read by name (pipe through grep then re-encode)
samtools view -h input.bam \
  | grep -E '^@|READNAME123' \
  | samtools view -b - > single_read.bam
```

#### Filter by tag values

```bash
# Filter by a specific tag using --tag-file (samtools >= 1.12)
samtools view -b --tag-file CB:barcodes.txt input.bam > tagged.bam

# Filter using -d for exact tag match (samtools >= 1.15)
samtools view -b -d CB:ACGTACGTACGTACGT-1 input.bam > one_barcode.bam

# Filter using -e expression (samtools >= 1.12)
samtools view -b -e '[NH] == 1' input.bam > unique_mappers.bam
samtools view -b -e '[AS] >= 100' input.bam > high_score.bam
```

#### Header operations

```bash
# View header only
samtools view -H input.bam

# Include header in SAM output
samtools view -h input.bam chr1:1000000-2000000

# Extract chromosome lengths from header
samtools view -H input.bam | grep '^@SQ' | awk '{print $2, $3}' | sed 's/[SL]N://g'

# Replace header
samtools reheader new_header.sam input.bam > reheadered.bam
```

### Sort, index, and format conversion

```bash
# Sort by coordinate (default)
samtools sort input.bam -o sorted.bam

# Sort by read name
samtools sort -n input.bam -o namesorted.bam

# Index a coordinate-sorted BAM (creates .bai)
samtools index sorted.bam

# Index with CSI for large chromosomes (>2^29 bp)
samtools index -c sorted.bam

# BAM to SAM
samtools view -h input.bam > output.sam

# SAM to BAM
samtools view -bS input.sam > output.bam

# BAM to CRAM (requires reference)
samtools view -C -T reference.fa input.bam > output.cram

# CRAM to BAM
samtools view -b -T reference.fa input.cram > output.bam

# Sort and index in one pipeline
samtools sort input.bam -o sorted.bam && samtools index sorted.bam

# Merge multiple BAMs
samtools merge merged.bam sample1.bam sample2.bam sample3.bam

# Multi-threaded operations
samtools sort -@ 8 input.bam -o sorted.bam
samtools view -@ 8 -b -F 2308 input.bam > primary.bam
samtools index -@ 8 sorted.bam
```

### bedtools operations

#### Intersect

```bash
# BED-BED intersection: regions in A that overlap B
bedtools intersect -a regions_a.bed -b regions_b.bed > overlap.bed

# BAM-BED intersection: reads overlapping BED regions
bedtools intersect -abam input.bam -b regions.bed > overlap.bam

# Report original A entry, not just the overlap
bedtools intersect -a regions_a.bed -b regions_b.bed -wa > original_a.bed

# Report both A and B entries for each overlap
bedtools intersect -a regions_a.bed -b regions_b.bed -wa -wb > both.bed

# Regions in A that do NOT overlap B (subtract/complement-like)
bedtools intersect -a regions_a.bed -b regions_b.bed -v > no_overlap.bed

# Reads NOT overlapping BED regions
bedtools intersect -abam input.bam -b regions.bed -v > non_overlap.bam

# Require minimum overlap fraction (50% of A must overlap B)
bedtools intersect -a regions_a.bed -b regions_b.bed -f 0.5 > overlap_50pct.bed

# Reciprocal overlap (both A and B must have 50% overlap)
bedtools intersect -a regions_a.bed -b regions_b.bed -f 0.5 -r > reciprocal.bed

# Count overlaps
bedtools intersect -a regions_a.bed -b regions_b.bed -c > counts.bed

# Multiple B files
bedtools intersect -a regions.bed -b peaks1.bed peaks2.bed peaks3.bed -wa -wb -names peaks1 peaks2 peaks3 > multi.bed

# Sorted input for large files (much faster, less memory)
bedtools intersect -a sorted_a.bed -b sorted_b.bed -sorted > overlap.bed
```

#### Merge

```bash
# Merge overlapping intervals (input must be sorted)
sort -k1,1 -k2,2n regions.bed | bedtools merge > merged.bed

# Merge with distance: merge intervals within 1000 bp of each other
sort -k1,1 -k2,2n regions.bed | bedtools merge -d 1000 > merged.bed

# Report count of merged intervals
sort -k1,1 -k2,2n regions.bed | bedtools merge -c 1 -o count > merged_counts.bed

# Merge and concatenate names
sort -k1,1 -k2,2n regions.bed | bedtools merge -c 4 -o collapse > merged_names.bed
```

#### Complement

```bash
# Get regions NOT covered by the BED file (requires genome file)
bedtools complement -i regions.bed -g genome.txt > complement.bed

# Create genome file from BAM header
samtools view -H input.bam \
  | grep '^@SQ' \
  | awk -F'\t' '{for(i=1;i<=NF;i++){if($i~/^SN:/){split($i,a,":");chr=a[2]}if($i~/^LN:/){split($i,a,":");len=a[2]}}print chr"\t"len}' \
  > genome.txt

# Alternatively with samtools
samtools idxstats input.bam | awk '{if($1!="*") print $1"\t"$2}' > genome.txt
```

#### Coverage and genome coverage

```bash
# Per-base genome coverage (BED output)
bedtools genomecov -ibam input.bam -bg > coverage.bedgraph

# Per-base genome coverage, split by strand
bedtools genomecov -ibam input.bam -bg -strand + > plus_coverage.bedgraph
bedtools genomecov -ibam input.bam -bg -strand - > minus_coverage.bedgraph

# Report histogram of coverage depths
bedtools genomecov -ibam input.bam > coverage_histogram.txt

# Coverage of BED regions
bedtools coverage -a regions.bed -b input.bam > region_coverage.bed

# BED to bedgraph-style coverage
bedtools genomecov -i regions.bed -g genome.txt -bg > coverage.bedgraph

# Only report regions with zero coverage
bedtools genomecov -ibam input.bam -bga | awk '$4 == 0' > zero_coverage.bed
```

#### BAM to BED conversion

```bash
# Basic conversion
bedtools bamtobed -i input.bam > reads.bed

# Split reads at splice junctions (RNA-seq, CIGAR N operations)
bedtools bamtobed -i input.bam -split > spliced_reads.bed

# Include CIGAR string
bedtools bamtobed -i input.bam -cigar > reads_cigar.bed

# BED12 format (retains blocks for spliced reads)
bedtools bamtobed -i input.bam -bed12 > reads_bed12.bed

# Convert from stdin
samtools view -b -F 2308 input.bam | bedtools bamtobed -i stdin > primary_reads.bed
```

#### Closest and window

```bash
# Find closest feature in B for each feature in A
bedtools closest -a query.bed -b reference.bed > closest.bed

# Report distance
bedtools closest -a query.bed -b reference.bed -d > closest_with_dist.bed

# Window: find features in B within a window around A
bedtools window -a genes.bed -b peaks.bed -w 10000 > nearby.bed

# Asymmetric window
bedtools window -a tss.bed -b peaks.bed -l 5000 -r 1000 > promoter_peaks.bed
```

#### Other useful bedtools operations

```bash
# Subtract: remove portions of A that overlap B
bedtools subtract -a regions_a.bed -b regions_b.bed > subtracted.bed

# Slop: extend intervals
bedtools slop -i regions.bed -g genome.txt -b 500 > extended.bed

# Asymmetric slop
bedtools slop -i tss.bed -g genome.txt -l 2000 -r 200 > promoters.bed

# Flank: get flanking regions (not the original interval)
bedtools flank -i regions.bed -g genome.txt -b 1000 > flanks.bed

# getfasta: extract sequences from a FASTA
bedtools getfasta -fi genome.fa -bed regions.bed -fo sequences.fa

# With strand awareness
bedtools getfasta -fi genome.fa -bed regions.bed -s -fo sequences_stranded.fa

# makewindows: create tiling windows across the genome
bedtools makewindows -g genome.txt -w 10000 > windows_10kb.bed

# Sliding windows with step
bedtools makewindows -g genome.txt -w 10000 -s 5000 > sliding_10kb_5kb.bed

# Shuffle: randomly place intervals
bedtools shuffle -i regions.bed -g genome.txt > shuffled.bed

# Shuffle excluding certain regions
bedtools shuffle -i regions.bed -g genome.txt -excl blacklist.bed > shuffled.bed

# Multi-intersect: identify shared/unique intervals across multiple files
bedtools multiinter -i sample1.bed sample2.bed sample3.bed > multiinter.bed
```

### Piping patterns

#### samtools-to-samtools pipes

```bash
# Filter, then sort, then index
samtools view -b -F 2308 -q 30 input.bam \
  | samtools sort -o filtered_sorted.bam - \
  && samtools index filtered_sorted.bam

# Name-sort, then fixmate, then coordinate-sort, then markdup
samtools sort -n input.bam \
  | samtools fixmate -m - - \
  | samtools sort - \
  | samtools markdup - deduped.bam \
  && samtools index deduped.bam
```

#### samtools-awk-samtools pipes

```bash
# Filter by a BAM tag using awk (generic pattern)
samtools view -h input.bam \
  | awk '$0 ~ /^@/ || $0 ~ /TAG:Z:VALUE/' \
  | samtools view -b - > filtered.bam

# Filter by mapping quality column (column 5 in SAM)
samtools view -h input.bam \
  | awk '$0 ~ /^@/ || $5 >= 30' \
  | samtools view -b - > high_mapq.bam

# Filter by alignment length
samtools view -h input.bam \
  | awk '$0 ~ /^@/ || length($10) >= 100' \
  | samtools view -b - > long_reads.bam

# Extract reads from a specific chromosome range then process
samtools view -h input.bam chr1:1-50000000 \
  | awk '$0 ~ /^@/ || $5 >= 20' \
  | samtools view -b - > chr1_first50M_q20.bam
```

#### samtools-bedtools pipes

```bash
# Filter BAM then intersect with BED
samtools view -b -F 2308 input.bam \
  | bedtools intersect -abam stdin -b regions.bed > primary_in_regions.bam

# Convert filtered BAM to BED
samtools view -b -F 2308 -q 30 input.bam \
  | bedtools bamtobed -i stdin > primary_q30.bed

# Get coverage of filtered reads
samtools view -b -F 2308 -q 30 input.bam \
  | bedtools genomecov -ibam stdin -bg > filtered_coverage.bedgraph
```

#### Complex multi-tool pipelines

```bash
# Count reads per gene for primary, high-quality alignments
samtools view -b -F 2308 -q 30 input.bam \
  | bedtools intersect -abam stdin -b genes.bed -wa -wb -bed \
  | awk '{print $NF}' \
  | sort | uniq -c | sort -rn > reads_per_gene.txt

# Extract and count unique barcodes from a region
samtools view input.bam chr1:1000000-2000000 \
  | grep -oP 'CB:Z:\K[^\t]+' \
  | sort | uniq -c | sort -rn > barcode_counts.txt

# Get insert size distribution for properly paired reads
samtools view -f 2 -F 2308 input.bam \
  | awk '{if($9>0) print $9}' \
  | sort -n | uniq -c > insert_sizes.txt
```

### 10x Genomics barcode filtering

10x Genomics data stores cell barcodes and UMIs in BAM tags:
- `CB:Z:` -- corrected cell barcode
- `CR:Z:` -- raw (uncorrected) cell barcode
- `UB:Z:` -- corrected UMI
- `UR:Z:` -- raw (uncorrected) UMI

```bash
# Filter reads by a single corrected barcode
samtools view -h input.bam \
  | awk '$0 ~ /^@/ || $0 ~ /CB:Z:ACGTACGTACGTACGT-1/' \
  | samtools view -b - > single_cell.bam

# Filter reads by a single raw barcode
samtools view -h input.bam \
  | awk '$0 ~ /^@/ || $0 ~ /CR:Z:ACGTACGTACGTACGT/' \
  | samtools view -b - > single_cell_raw.bam

# Filter by a list of barcodes (using grep -f)
samtools view -h input.bam \
  | grep -E '^@' > header.sam
samtools view input.bam \
  | grep -f barcode_patterns.txt >> header.sam
samtools view -b header.sam > multi_cell.bam && rm header.sam

# More efficient: barcode list with awk
samtools view -h input.bam \
  | awk 'BEGIN{while(getline<"barcodes.txt") bc[$1]=1}
         /^@/{print; next}
         {for(i=12;i<=NF;i++){if($i~/^CB:Z:/){split($i,a,":"); if(a[3] in bc) print}}}' \
  | samtools view -b - > multi_cell.bam

# Using samtools --tag-file (samtools >= 1.12, most efficient)
samtools view -b --tag-file CB:barcodes.txt input.bam > multi_cell.bam

# Using samtools -d for single barcode (samtools >= 1.15)
samtools view -b -d CB:ACGTACGTACGTACGT-1 input.bam > single_cell.bam

# Extract all unique corrected barcodes
samtools view input.bam | grep -oP 'CB:Z:\K[^\t]+' | sort -u > all_barcodes.txt

# Count reads per barcode
samtools view input.bam | grep -oP 'CB:Z:\K[^\t]+' | sort | uniq -c | sort -rn > barcode_read_counts.txt

# Filter by barcode and region simultaneously
samtools view -h input.bam chr1:1000000-2000000 \
  | awk '$0 ~ /^@/ || $0 ~ /CB:Z:ACGTACGTACGTACGT-1/' \
  | samtools view -b - > cell_region.bam
```

### Coverage and statistics

```bash
# Quick alignment summary
samtools flagstat input.bam

# Per-chromosome read counts and lengths
samtools idxstats input.bam

# Per-base depth at every position
samtools depth input.bam > depth.txt

# Depth only in specific regions
samtools depth -b regions.bed input.bam > region_depth.txt

# Depth including zero-coverage positions
samtools depth -a input.bam > depth_with_zeros.txt

# Depth with max depth limit removed (default is 8000)
samtools depth -d 0 input.bam > depth_unlimited.txt

# Coverage summary per chromosome
samtools coverage input.bam

# Coverage with histogram
samtools coverage --histogram input.bam

# Mean coverage for specific regions
samtools depth -b regions.bed input.bam \
  | awk '{sum[$1]+=$3; count[$1]++} END{for(chr in sum) print chr, sum[chr]/count[chr]}'

# Stats (comprehensive alignment statistics)
samtools stats input.bam > stats.txt

# Plot stats (requires plot-bamstats and gnuplot)
plot-bamstats -p output_prefix stats.txt
```

## Key concepts

### BAM flags bitfield

SAM flags are a 12-bit integer where each bit independently encodes an alignment property. To combine flags, add their decimal values. For example, to exclude reads that are unmapped (4), secondary (256), or supplementary (2048), use `-F 2308` (4 + 256 + 2048). The `-F` flag excludes reads where ANY specified bit is set. The `-f` flag requires ALL specified bits to be set. The `-G` flag (if available) excludes reads where ALL specified bits are set.

### Coordinate systems: 0-based BED vs 1-based SAM

This is one of the most common sources of off-by-one errors in genomics:

- **BED format**: 0-based, half-open. The interval `chr1  0  100` covers bases at positions 0-99 (first 100 bases). The start is inclusive, the end is exclusive.
- **SAM/BAM format**: 1-based, closed. Position 1 is the first base of the chromosome. A read at POS=1 starts at the very first base.
- **VCF format**: 1-based, closed.
- **GFF/GTF format**: 1-based, closed.

Conversion: BED start = SAM POS - 1. BED end = SAM POS + read_length - 1 (for ungapped alignments).

When working with `bedtools intersect -abam`, bedtools handles the coordinate conversion internally. But when extracting positions from SAM with awk and feeding them into BED-based tools, you must subtract 1 from the start coordinate.

### Sorted and indexed requirements

- **samtools view with regions** (e.g., `chr1:1-1000`): requires coordinate-sorted and indexed BAM (.bai or .csi index)
- **samtools view -L** (BED file): requires coordinate-sorted and indexed BAM
- **bedtools intersect -sorted**: requires both inputs sorted by chromosome then position (using `sort -k1,1 -k2,2n` for BED)
- **bedtools merge**: requires sorted input
- **bedtools complement**: requires sorted input
- **samtools index**: requires coordinate-sorted BAM
- **samtools markdup**: requires name-sorted input (or coordinate-sorted with fixmate applied after name-sorting)
- **bedtools genomecov -ibam**: does NOT require indexing but does require coordinate-sorted input

To sort a BED file for bedtools:
```bash
sort -k1,1 -k2,2n input.bed > sorted.bed
```

### CRAM vs BAM

CRAM files are reference-based compressed alignments. They are smaller than BAM but require the reference FASTA for most operations. Set the reference via:
```bash
# Per-command
samtools view -T reference.fa input.cram

# Via environment variable
export REF_PATH=/path/to/references/%2s/%2s/%s
```

## Common pitfalls

1. **Forgetting to index after sorting.** Many samtools operations silently fail or error when the BAM is not indexed. Always run `samtools index` after `samtools sort`.

2. **Using `-F 4` when you mean `-F 2308`.** `-F 4` removes unmapped reads but still includes secondary and supplementary alignments, inflating read counts. For most analyses, use `-F 2308` to keep only primary mapped alignments.

3. **Piping SAM without the header.** When piping through awk/grep and back into `samtools view -b`, you must preserve the header lines (lines starting with `@`). Always use `samtools view -h` and include `$0 ~ /^@/` in awk conditions.

4. **Off-by-one errors between BED and SAM coordinates.** BED is 0-based half-open; SAM is 1-based. When manually extracting coordinates from SAM and creating BED intervals, subtract 1 from the start.

5. **Not sorting BED files before bedtools merge/complement.** These operations require sorted input. Use `sort -k1,1 -k2,2n` to sort by chromosome name then numerically by start position.

6. **Exceeding default depth cap in samtools depth.** The default maximum depth is 8000. Use `-d 0` to remove the cap if you need accurate depth at high-coverage sites.

7. **Using samtools without `-@` threads for large files.** Most samtools subcommands accept `-@ N` for multithreading. This can dramatically speed up sort, view, index, merge, and other I/O-heavy operations.

8. **Forgetting `-b` flag when piping samtools output to bedtools.** If you pipe SAM (not BAM) into bedtools with `-abam`, it will fail. Either use `-b` in `samtools view` to output BAM, or use bedtools `-a stdin` with SAM format where supported.

9. **Assuming read name order equals coordinate order.** After `samtools sort -n` (name sort), the file is no longer coordinate-sorted and cannot be indexed or used for region queries.

10. **Ignoring the chromosome naming mismatch.** If your BAM uses `chr1` but your BED uses `1` (or vice versa), intersections will silently return zero results. Check chromosome naming with `samtools idxstats input.bam | head` and ensure consistency across all input files.

11. **Using `bedtools intersect -abam` with an unsorted BAM when using `-sorted`.** The `-sorted` flag assumes both inputs are sorted. If the BAM is not coordinate-sorted, the results will be incomplete or wrong, often without an error message.

12. **Not accounting for strand in bedtools getfasta.** Without `-s`, sequences are always extracted from the forward strand regardless of the strand column in the BED file. Use `-s` when strand matters (e.g., for motif analysis or transcript sequences).
