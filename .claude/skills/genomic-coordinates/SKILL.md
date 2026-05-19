---
name: genomic-coordinates
description: Genomic coordinate systems reference. Convert between 0-based BED and 1-based GFF/SAM/VCF, parse GTF/GFF3 annotations, perform liftOver between assemblies, and handle chromosome naming conventions.
license: MIT license
metadata:
    skill-author: VFranke
---

# Genomic Coordinate Systems

## Overview

Coordinate systems in genomics are a persistent source of confusion and off-by-one bugs. Different file formats, tools, and programming libraries use different conventions for representing genomic intervals. Some are 0-based, some are 1-based. Some use half-open intervals, others use closed intervals. A position that is 100 in a BED file is 101 in a GFF file, and getting this wrong silently produces incorrect results -- shifted annotations, missed overlaps, wrong sequences extracted.

This skill provides a definitive reference for converting between coordinate systems, parsing annotation files, lifting coordinates between genome assemblies, and handling chromosome naming conventions.

## When to Use

- Converting intervals between BED, GFF/GTF, SAM/BAM, or VCF formats
- Parsing GTF or GFF3 annotation files and extracting gene features
- Lifting coordinates from one genome assembly to another (e.g., hg19 to hg38)
- Reconciling chromosome naming between files from different sources (UCSC vs Ensembl vs NCBI)
- Computing promoter regions, flanking sequences, or overlaps between feature sets
- Debugging off-by-one errors in genomic pipelines
- Writing coordinate-aware code in Python (pysam, pybedtools) or R (GenomicRanges, rtracklayer)

## Quick Reference: Coordinate Systems

Consider a 3-base feature covering the 4th, 5th, and 6th nucleotides of a chromosome:

```
Nucleotide position (1-based):  1  2  3  4  5  6  7  8  9
                                          [=====]
```

| Format / Tool       | Base  | Interval Type      | Start | End | Representation |
|---------------------|-------|--------------------|-------|-----|----------------|
| **BED**             | 0     | Half-open [s, e)   | 3     | 6   | `chr1  3  6`   |
| **SAM/BAM**         | 1     | Closed [s, e]      | 4     | 6   | `POS=4`        |
| **VCF**             | 1     | Single position    | 4     | --  | `POS=4`        |
| **GFF/GTF**         | 1     | Closed [s, e]      | 4     | 6   | `chr1  4  6`   |
| **UCSC browser**    | 1     | Display (0 internal)| 4    | 6   | Shows `4-6`    |
| **Pysam**           | 0     | Half-open [s, e)   | 3     | 6   | `start=3, end=6` |
| **R GenomicRanges** | 1     | Closed [s, e]      | 4     | 6   | `IRanges(4, 6)` |
| **bedtools**        | 0     | Half-open (BED)    | 3     | 6   | Follows BED input |

### Key Conversion Rules

```
BED_start = GFF_start - 1       GFF_start = BED_start + 1
BED_end   = GFF_end             GFF_end   = BED_end
BED_start = SAM_POS - 1         SAM_POS   = BED_start + 1
```

The end coordinate is the same between BED (half-open) and GFF (closed) because half-open excludes the end position while closed includes it -- they resolve to the same last base.

## Core Capabilities

### GTF/GFF3 Parsing

#### Format Differences

**GTF (GFF2)** and **GFF3** share the same 9-column tab-delimited structure but differ in the attribute column (column 9).

```
# GTF attribute format: key "value"; pairs separated by semicolons
gene_id "ENSG00000139618"; gene_name "BRCA2"; transcript_id "ENST00000380152";

# GFF3 attribute format: key=value pairs separated by semicolons, URL-encoded special chars
ID=gene:ENSG00000139618;Name=BRCA2;biotype=protein_coding
```

**Nine columns shared by both formats:**

```
seqname  source  feature  start  end  score  strand  frame  attributes
chr1     HAVANA  gene     11869  14409  .     +       .      gene_id "ENSG00000223972"; ...
```

Both formats use **1-based, closed** coordinates.

#### Gene/Transcript/Exon Hierarchy

GTF/GFF3 files encode a hierarchical structure:

```
gene
  +-- transcript (mRNA)
        +-- exon
        +-- CDS
        +-- five_prime_UTR  (GFF3) / UTR (some GTFs)
        +-- three_prime_UTR (GFF3)
```

In GFF3, the hierarchy is explicit via `Parent` attributes. In GTF, it is implicit via shared `gene_id` and `transcript_id` attributes.

#### Parsing in R

```r
library(rtracklayer)

# Import GTF -- returns a GRanges object
gtf <- rtracklayer::import("annotation.gtf")

# Filter by feature type
genes <- gtf[gtf$type == "gene"]
exons <- gtf[gtf$type == "exon"]
transcripts <- gtf[gtf$type == "transcript"]

# Access attributes
genes$gene_id
genes$gene_name
exons$transcript_id
```

#### Parsing in Python

```python
import pandas as pd

# Quick GTF parsing with pandas
col_names = ['seqname', 'source', 'feature', 'start', 'end',
             'score', 'strand', 'frame', 'attributes']
gtf = pd.read_csv('annotation.gtf', sep='\t', comment='#',
                   header=None, names=col_names)

# Extract gene_id from attributes
gtf['gene_id'] = gtf['attributes'].str.extract(r'gene_id "([^"]+)"')

# Using gffutils for proper hierarchical parsing
import gffutils
db = gffutils.create_db('annotation.gff3', 'annotation.db',
                         merge_strategy='merge')
for gene in db.features_of_type('gene'):
    for transcript in db.children(gene, featuretype='mRNA'):
        for exon in db.children(transcript, featuretype='exon'):
            print(gene.id, transcript.id, exon.start, exon.end)
```

### Converting Between Formats

#### BED to GFF

```bash
# BED (0-based, half-open) -> GFF (1-based, closed)
# Add 1 to start; end stays the same
awk 'BEGIN{OFS="\t"} {print $1, "bed2gff", "region", $2+1, $3, ".", ".", ".", "Name="$4}' input.bed > output.gff
```

#### GFF to BED

```bash
# GFF (1-based, closed) -> BED (0-based, half-open)
# Subtract 1 from start; end stays the same
awk 'BEGIN{OFS="\t"} !/^#/ {print $1, $4-1, $5, $9, $6, $7}' input.gff > output.bed
```

#### In R

```r
library(rtracklayer)

# Import GFF, export as BED -- rtracklayer handles coordinate conversion automatically
gr <- import("features.gff")
export(gr, "features.bed", format="BED")

# Import BED, export as GFF
gr <- import("features.bed")
export(gr, "features.gff", format="GFF3")
```

#### In Python with pybedtools

```python
import pybedtools

# pybedtools uses BED-style (0-based) internally
bed = pybedtools.BedTool('features.bed')

# Convert to GFF-style coordinates when needed
for feature in bed:
    gff_start = feature.start + 1  # 0-based -> 1-based
    gff_end = feature.end           # same value
```

### LiftOver Between Assemblies

LiftOver converts genomic coordinates from one genome assembly to another (e.g., hg19/GRCh37 to hg38/GRCh38, or mm9 to mm10).

#### UCSC liftOver (command line)

```bash
# Download chain file from UCSC
wget https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz

# Convert BED file -- input must be BED format (0-based)
liftOver input_hg19.bed hg19ToHg38.over.chain.gz output_hg38.bed unmapped.bed

# The unmapped.bed file contains regions that could not be mapped
# Check it to ensure critical regions were not lost
wc -l unmapped.bed
```

#### CrossMap (Python-based)

```bash
# Supports BED, GFF, GTF, SAM, BAM, VCF, BigWig, and Wiggle
pip install CrossMap

# Convert BED
CrossMap bed hg19ToHg38.over.chain.gz input.bed output.bed

# Convert VCF (requires reference FASTA of target assembly)
CrossMap vcf hg19ToHg38.over.chain.gz input.vcf hg38.fa output.vcf

# Convert BAM
CrossMap bam hg19ToHg38.over.chain.gz input.bam output.bam
```

#### R rtracklayer::liftOver

```r
library(rtracklayer)

# Import chain file
chain <- import.chain("hg19ToHg38.over.chain")

# LiftOver a GRanges object
gr_hg19 <- GRanges(seqnames="chr1", ranges=IRanges(start=1000, end=2000))
gr_hg38 <- liftOver(gr_hg19, chain)

# Result is a GRangesList -- some regions may map to multiple locations
# or not map at all
gr_hg38 <- unlist(gr_hg38)
```

#### Chain File Sources

| Conversion       | Chain file URL prefix                                                  |
|------------------|------------------------------------------------------------------------|
| hg19 -> hg38     | `https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/`           |
| hg38 -> hg19     | `https://hgdownload.soe.ucsc.edu/goldenPath/hg38/liftOver/`           |
| mm9  -> mm10     | `https://hgdownload.soe.ucsc.edu/goldenPath/mm9/liftOver/`            |
| mm10 -> mm39     | `https://hgdownload.soe.ucsc.edu/goldenPath/mm10/liftOver/`           |

### Chromosome Naming Conventions

Different data sources use different chromosome naming schemes:

| Source      | Autosomes | Sex chr  | Mitochondrial | Example accession    |
|-------------|-----------|----------|---------------|----------------------|
| **UCSC**    | chr1      | chrX     | chrM          | --                   |
| **Ensembl** | 1         | X        | MT            | --                   |
| **NCBI/RefSeq** | NC_000001.11 | NC_000023.11 | NC_012920.1 | GenBank accessions |

#### Fixing chromosome names in R

```r
library(GenomeInfoDb)

# Check current style
seqlevelsStyle(gr)  # "UCSC", "NCBI", or "Ensembl"

# Convert between styles
seqlevelsStyle(gr) <- "UCSC"     # 1 -> chr1
seqlevelsStyle(gr) <- "Ensembl"  # chr1 -> 1

# Manual renaming
seqlevels(gr) <- sub("^chr", "", seqlevels(gr))   # UCSC -> Ensembl
seqlevels(gr) <- paste0("chr", seqlevels(gr))      # Ensembl -> UCSC
```

#### Fixing chromosome names in BAM/BED (command line)

```bash
# Add "chr" prefix to a BED file
sed 's/^/chr/' input.bed > output.bed

# Remove "chr" prefix
sed 's/^chr//' input.bed > output.bed

# For BAM files: reheader with new chromosome names
samtools view -H input.bam | sed 's/SN:\([0-9XY]\)/SN:chr\1/' | \
    sed 's/SN:MT/SN:chrM/' | samtools reheader - input.bam > output.bam

# Using a chromosome name mapping file
# Create mapping: old_name\tnew_name
samtools view -H input.bam | grep '^@SQ' | \
    awk '{print $2}' | sed 's/SN://' | \
    awk '{print $1"\tchr"$1}' > chr_map.txt
# Then use bcftools or picard to rename
```

### Coordinate Arithmetic

#### Common Operations in R (GenomicRanges)

```r
library(GenomicRanges)

# Create GRanges (1-based, closed)
gr <- GRanges(seqnames="chr1",
              ranges=IRanges(start=c(100, 200, 400),
                             end=c(150, 300, 500)),
              strand="+")

# Promoter regions (upstream of TSS)
promoters(gr, upstream=2000, downstream=200)

# Flank: get flanking regions
flank(gr, width=100, start=TRUE)   # 100bp upstream
flank(gr, width=100, start=FALSE)  # 100bp downstream

# Resize: resize from start or end
resize(gr, width=1, fix="start")   # TSS (single base)
resize(gr, width=1, fix="end")     # TTS (single base)

# Shift
shift(gr, shift=50)

# Reduce: merge overlapping ranges
reduce(gr)

# Find overlaps
query <- GRanges("chr1", IRanges(120, 250))
hits <- findOverlaps(query, gr)
subsetByOverlaps(gr, query)

# Gaps: find regions NOT covered
gaps(gr)

# Coverage
coverage(gr)
```

#### Common Operations with bedtools

```bash
# Overlap / intersect (both files must use same coordinate system)
bedtools intersect -a features.bed -b peaks.bed

# Intersect with reporting original entries
bedtools intersect -a features.bed -b peaks.bed -wa -wb

# Subtract: remove overlapping regions
bedtools subtract -a features.bed -b blacklist.bed

# Flanking regions
bedtools flank -i genes.bed -g chromsizes.txt -l 2000 -r 0  # 2kb upstream

# Slop: extend intervals on both sides
bedtools slop -i peaks.bed -g chromsizes.txt -b 100

# Closest feature
bedtools closest -a tss.bed -b enhancers.bed -d  # -d reports distance

# Merge overlapping intervals (input must be sorted)
sort -k1,1 -k2,2n input.bed | bedtools merge -i -

# Complement: regions NOT in the input
bedtools complement -i features.bed -g chromsizes.txt

# Window: find features within a window
bedtools window -a genes.bed -b snps.bed -w 10000  # 10kb window
```

### Extracting Features from GTF

#### Genes

```r
library(rtracklayer)
gtf <- import("gencode.v38.annotation.gtf")
genes <- gtf[gtf$type == "gene"]
```

#### Exons and Introns

```r
# Exons per transcript
exons <- gtf[gtf$type == "exon"]
exons_by_tx <- split(exons, exons$transcript_id)

# Introns: gaps between exons within each transcript
introns_by_tx <- psetdiff(range(exons_by_tx), exons_by_tx)
introns <- unlist(introns_by_tx)
```

#### UTRs

```r
# 5' and 3' UTRs from GFF3
utr5 <- gtf[gtf$type == "five_prime_UTR"]
utr3 <- gtf[gtf$type == "three_prime_UTR"]

# From GTF where UTRs are marked as "UTR", determine 5'/3' by position relative to CDS
utrs <- gtf[gtf$type == "UTR"]
cds  <- gtf[gtf$type == "CDS"]
```

#### TSS (Transcription Start Sites)

```r
# TSS is the 5' end of each transcript, strand-aware
transcripts <- gtf[gtf$type == "transcript"]
tss <- resize(transcripts, width=1, fix="start")  # Single-base TSS

# Promoter regions around TSS
promoter_regions <- promoters(transcripts, upstream=2000, downstream=200)
```

#### In awk (command line)

```bash
# Extract gene entries from GTF
awk '$3 == "gene"' annotation.gtf > genes.gtf

# Extract all exons and convert to BED
awk 'BEGIN{OFS="\t"} $3 == "exon" {
    match($0, /gene_name "([^"]+)"/, gn);
    print $1, $4-1, $5, gn[1], ".", $7
}' annotation.gtf > exons.bed

# Extract TSS as BED (strand-aware)
awk 'BEGIN{OFS="\t"} $3 == "transcript" {
    match($0, /transcript_id "([^"]+)"/, tid);
    if ($7 == "+") print $1, $4-1, $4, tid[1], ".", $7;
    else print $1, $5-1, $5, tid[1], ".", $7;
}' annotation.gtf > tss.bed
```

## Conversion Cheat Sheet

### Example: A feature at chr1:1000-2000 (1-based, closed -- e.g., from GFF)

| Target Format        | Start  | End   | Notes                           |
|----------------------|--------|-------|---------------------------------|
| GFF/GTF (1-based)    | 1000   | 2000  | Original                        |
| BED (0-based)        | 999    | 2000  | start - 1; end unchanged        |
| SAM POS (1-based)    | 1000   | --    | POS = leftmost mapping position |
| VCF POS (1-based)    | 1000   | --    | POS = variant position          |
| Pysam (0-based)      | 999    | 2000  | Same as BED                     |
| R IRanges (1-based)  | 1000   | 2000  | Same as GFF                     |

### Width Calculations

```
BED:    width = end - start           (2000 - 999 = 1001)
GFF:    width = end - start + 1       (2000 - 1000 + 1 = 1001)
```

Both give the same width (1001 bp) when coordinates are correctly represented.

## Common Pitfalls

### 1. Off-by-one errors when converting between systems

The single most common bug. Always ask: is this format 0-based or 1-based? Is the interval half-open or closed?

```bash
# WRONG: naively copying GFF coordinates into a BED file
# GFF says gene starts at position 1000 -- putting 1000 in BED means position 1001 in 1-based
# CORRECT: subtract 1 from start when going GFF -> BED
```

### 2. Forgetting BED is half-open

In BED format, `chr1  100  200` covers bases 101 through 200 (1-based) -- it does NOT include the base at position 100 (0-based index 100 means 1-based 101) and DOES include up to but not including position 200 in 0-based terms.

```
BED:  chr1  100  103   ->  covers 3 bases (positions 101, 102, 103 in 1-based)
                           NOT 4 bases
```

### 3. Chromosome prefix mismatches

Mixing files with different naming conventions silently produces empty results:

```bash
# This finds ZERO overlaps if peaks.bed uses "chr1" but genes.bed uses "1"
bedtools intersect -a peaks.bed -b genes.bed
# No error, no warning -- just empty output

# Always check chromosome names first
head -1 peaks.bed   # chr1  1000  2000
head -1 genes.bed   # 1     5000  6000
# Fix: add/remove "chr" prefix before intersecting
```

### 4. Mixing coordinate systems in the same pipeline

```bash
# WRONG: using GFF coordinates directly with bedtools (which expects BED)
awk '{print $1, $4, $5}' annotation.gff | bedtools intersect -a - -b peaks.bed
# This shifts everything by 1 base!

# CORRECT: convert GFF to BED coordinates first
awk 'BEGIN{OFS="\t"} {print $1, $4-1, $5}' annotation.gff | bedtools intersect -a - -b peaks.bed
```

### 5. SAM/BAM POS is 1-based but pysam is 0-based

```python
import pysam

bam = pysam.AlignmentFile("aligned.bam", "rb")
for read in bam:
    # read.reference_start is 0-based (pysam convention)
    # read.reference_end is 0-based, half-open
    # The SAM spec POS field is 1-based
    sam_pos = read.reference_start + 1  # Convert to SAM POS
```

### 6. VCF indels and the anchor base

VCF represents indels with an anchor base before the actual variant. For a deletion of "AT" at position 100:

```
#CHROM  POS  REF   ALT
chr1    99   GAT   G
```

POS (99) is the anchor base, not the first deleted base. The deletion actually occurs at positions 100-101.

### 7. Strand-awareness for TSS and promoters

The TSS is at the **start** for `+` strand genes and at the **end** for `-` strand genes:

```r
# WRONG: always using start position
tss_wrong <- resize(genes, width=1, fix="start")  # Only correct for + strand

# CORRECT: resize with fix="start" is strand-aware in GenomicRanges
# fix="start" means the 5' end, which IS strand-aware -- this is actually correct
tss <- resize(genes, width=1, fix="start")  # Correct: respects strand
```

### 8. Sorted input requirements

Many tools require sorted input and will produce wrong results or errors on unsorted data:

```bash
# bedtools merge requires sorted input
sort -k1,1 -k2,2n input.bed | bedtools merge -i -

# bedtools intersect is faster with sorted input
bedtools intersect -a sorted_a.bed -b sorted_b.bed -sorted

# tabix indexing requires bgzipped, sorted input
sort -k1,1 -k2,2n input.bed | bgzip > input.bed.gz
tabix -p bed input.bed.gz
```
