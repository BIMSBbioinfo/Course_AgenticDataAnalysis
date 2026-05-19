---
name: 10x-genomics
description: 10x Genomics single-cell toolkit. Process Cell Ranger outputs, handle barcode/UMI demultiplexing, work with feature-barcode matrices, filter cells by barcodes, and parse 10x BAM tags (CB, UB, CR, UR).
license: MIT license
metadata:
    skill-author: VFranke
---

# 10x Genomics Single-Cell RNA-seq Toolkit

## Overview

This skill provides comprehensive guidance for working with 10x Genomics Chromium single-cell RNA-seq data. It covers the full workflow from Cell Ranger processing through downstream loading in R and Python, including BAM file manipulation, barcode handling, feature-barcode matrix I/O, and alternative alignment with STARsolo.

10x Chromium technology partitions individual cells into gel bead-in-emulsion (GEM) droplets, where each cell is tagged with a unique cell barcode and each mRNA molecule receives a unique molecular identifier (UMI). This enables digital counting of transcripts per gene per cell at single-cell resolution.

## When to Use

Use this skill when you need to:

- Process raw 10x Chromium scRNA-seq FASTQ files through Cell Ranger or STARsolo
- Navigate and understand Cell Ranger output directory structures
- Load feature-barcode matrices into R (Seurat, DropletUtils) or Python (Scanpy)
- Extract reads for specific cell barcodes from 10x BAM files
- Parse and filter on 10x-specific BAM tags (CB, UB, CR, UR, etc.)
- Aggregate multiple Cell Ranger runs
- Run multi-library analyses (Cell Ranger multi)
- Distinguish filtered vs. raw matrices and understand empty droplet filtering
- Detect doublets in single-cell data
- Use STARsolo as an open-source alternative to Cell Ranger

## Quick Start

### Minimal Cell Ranger count run

```bash
cellranger count \
  --id=sample_01 \
  --transcriptome=/path/to/refdata-gex-GRCh38-2024-A \
  --fastqs=/path/to/fastqs/ \
  --sample=Sample01 \
  --localcores=16 \
  --localmem=64
```

### Load the filtered matrix in R (Seurat)

```r
library(Seurat)
mat <- Read10X(data.dir = "sample_01/outs/filtered_feature_bc_matrix/")
sobj <- CreateSeuratObject(counts = mat, project = "sample_01", min.cells = 3, min.features = 200)
```

### Load the filtered matrix in Python (Scanpy)

```python
import scanpy as sc
adata = sc.read_10x_mtx("sample_01/outs/filtered_feature_bc_matrix/", var_names="gene_symbols")
# or from HDF5
adata = sc.read_10x_h5("sample_01/outs/filtered_feature_bc_matrix.h5")
```

## Core Capabilities

### Cell Ranger Output Directory Structure

After a successful `cellranger count` run, the output is organized under the `outs/` directory:

```
sample_01/
  outs/
    filtered_feature_bc_matrix/       # Matrix containing only cell-associated barcodes
      barcodes.tsv.gz
      features.tsv.gz
      matrix.mtx.gz
    filtered_feature_bc_matrix.h5     # Same data in HDF5 format
    raw_feature_bc_matrix/            # Matrix containing ALL detected barcodes (including empty droplets)
      barcodes.tsv.gz
      features.tsv.gz
      matrix.mtx.gz
    raw_feature_bc_matrix.h5          # Same data in HDF5 format
    possorted_genome_bam.bam          # Position-sorted, annotated BAM file
    possorted_genome_bam.bam.bai      # BAM index
    molecule_info.h5                  # Per-molecule information (barcode, UMI, gene, counts)
    metrics_summary.csv               # Run summary metrics
    web_summary.html                  # Interactive HTML summary report
    cloupe.cloupe                     # Loupe Browser file
```

Key points about these files:

- **filtered_feature_bc_matrix/**: Contains only barcodes that Cell Ranger has called as valid cells. This is the default starting point for most analyses.
- **raw_feature_bc_matrix/**: Contains every barcode that was observed, including ambient RNA / empty droplets. Use this when you want to perform your own cell calling (e.g., with `emptyDrops()` from DropletUtils).
- **possorted_genome_bam.bam**: Reads aligned to the genome, sorted by position, with 10x-specific tags added (see BAM Tags section).
- **molecule_info.h5**: Used internally by `cellranger aggr` for normalization across samples. Also useful for custom analyses of per-molecule data.

### Feature-Barcode Matrix Formats

#### MEX (Market Exchange) Format

The MEX format consists of three files:

| File | Description |
|------|-------------|
| `matrix.mtx.gz` | Sparse matrix in Matrix Market format (genes x barcodes) |
| `barcodes.tsv.gz` | One barcode per line (e.g., `AAACCTGAGAAGGCCT-1`) |
| `features.tsv.gz` | Tab-separated: gene ID, gene name, feature type (e.g., `ENSG00000243485\tMIR1302-2HG\tGene Expression`) |

In Cell Ranger v3+, `genes.tsv` was renamed to `features.tsv` to support multi-modal data (Gene Expression, Antibody Capture, CRISPR Guide Capture, etc.). Older pipelines (v2) use `genes.tsv` with only two columns.

Reading MEX format manually in R:

```r
library(Matrix)
mat <- readMM("matrix.mtx.gz")
barcodes <- read.table("barcodes.tsv.gz", header = FALSE)$V1
features <- read.table("features.tsv.gz", header = FALSE, sep = "\t")
rownames(mat) <- features$V2  # gene symbols
colnames(mat) <- barcodes
```

Reading MEX format manually in Python:

```python
import scipy.io
import pandas as pd

mat = scipy.io.mmread("matrix.mtx.gz").tocsc()
barcodes = pd.read_csv("barcodes.tsv.gz", header=None)[0].values
features = pd.read_csv("features.tsv.gz", header=None, sep="\t")
```

#### HDF5 Format (.h5)

The `.h5` file contains the same data as MEX in a single file, which is faster to read for large datasets. It uses the HDF5 format with a `/matrix` group containing:

- `/matrix/barcodes` - cell barcodes
- `/matrix/data` - non-zero count values
- `/matrix/indices` - row indices of non-zero entries
- `/matrix/indptr` - column pointer array
- `/matrix/shape` - matrix dimensions
- `/matrix/features/id` - gene/feature IDs
- `/matrix/features/name` - gene/feature names
- `/matrix/features/feature_type` - feature types

Reading HDF5 in R:

```r
# With Seurat
library(Seurat)
mat <- Read10X_h5("filtered_feature_bc_matrix.h5")

# With DropletUtils
library(DropletUtils)
sce <- read10xCounts("filtered_feature_bc_matrix.h5")
```

Reading HDF5 in Python:

```python
import scanpy as sc
adata = sc.read_10x_h5("filtered_feature_bc_matrix.h5")

# Or manually with h5py
import h5py
with h5py.File("filtered_feature_bc_matrix.h5", "r") as f:
    barcodes = f["matrix/barcodes"][:]
    data = f["matrix/data"][:]
    indices = f["matrix/indices"][:]
    indptr = f["matrix/indptr"][:]
    shape = f["matrix/shape"][:]
    gene_names = f["matrix/features/name"][:]
```

### BAM Tags

The `possorted_genome_bam.bam` file contains standard alignment fields plus 10x-specific tags. These tags encode barcode, UMI, and gene annotation information for each read.

| Tag | Type | Description |
|-----|------|-------------|
| `CB:Z` | String | **Corrected cell barcode.** Error-corrected barcode sequence with suffix (e.g., `AAACCTGAGAAGGCCT-1`). Only present if the barcode was successfully corrected against the whitelist. This is the tag to use for cell assignment. |
| `CR:Z` | String | **Raw cell barcode.** The barcode sequence as read from the sequencer, before any error correction. Always present. |
| `CY:Z` | String | Cell barcode quality scores (Phred). |
| `UB:Z` | String | **Corrected UMI.** Error-corrected UMI sequence. Only present if the UMI was successfully corrected. |
| `UR:Z` | String | **Raw UMI.** The UMI sequence as read from the sequencer. |
| `UY:Z` | String | UMI quality scores (Phred). |
| `RE:A` | Character | **Region type.** Where the read aligned: `E` (exonic), `N` (intronic), `I` (intergenic). |
| `xf:i` | Integer | **Extra flags.** Bitwise flags encoding various QC filters. A value of `25` (bits 0, 3, 4 set) indicates a confidently mapped, valid-barcode, valid-UMI read that contributes to the count matrix. |
| `GN:Z` | String | **Gene name(s).** Semicolon-separated gene symbols the read is assigned to. |
| `GX:Z` | String | **Gene ID(s).** Semicolon-separated Ensembl (or equivalent) gene IDs. |
| `TX:Z` | String | Transcript(s) the read is compatible with, with strand and position info. |
| `AN:Z` | String | Antisense gene name(s). |

Viewing tags in a BAM file:

```bash
# View the first 5 alignments with all tags
samtools view possorted_genome_bam.bam | head -5

# Extract specific tags for inspection
samtools view possorted_genome_bam.bam | awk '{for(i=12;i<=NF;i++) if($i ~ /^CB:Z:/) print $i}' | head
```

### Barcode Filtering: Extracting Reads for Specific Cell Barcodes

A common task is subsetting a 10x BAM to retain only reads from a specific set of cell barcodes (e.g., a cluster of interest).

#### Method 1: samtools + grep (simple, moderate speed)

```bash
# Create a barcode list file (one barcode per line, with the -1 suffix)
# barcodes_of_interest.txt:
# AAACCTGAGAAGGCCT-1
# AAACCTGAGATCCCGC-1
# ...

# Extract reads matching those barcodes via the CB:Z tag
samtools view -h possorted_genome_bam.bam \
  | grep -F -f <(sed 's/^/CB:Z:/' barcodes_of_interest.txt) \
  | samtools view -bS -o subset.bam -

# Do not forget the header lines (important for downstream tools)
# A more robust version that always keeps headers:
samtools view -h possorted_genome_bam.bam \
  | awk -v barcodes="barcodes_of_interest.txt" '
    BEGIN { while ((getline line < barcodes) > 0) bc["CB:Z:" line] = 1 }
    /^@/ { print; next }
    { for (i = 12; i <= NF; i++) if ($i in bc) { print; break } }
  ' \
  | samtools view -bS -o subset.bam -

# Index the result
samtools index subset.bam
```

#### Method 2: subset-bam (10x Genomics tool, fastest)

```bash
# 10x provides a dedicated tool (if available)
subset-bam \
  --bam possorted_genome_bam.bam \
  --cell-barcodes barcodes_of_interest.txt \
  --out-bam subset.bam \
  --cores 8
```

#### Method 3: Python with pysam

```python
import pysam

barcodes = set()
with open("barcodes_of_interest.txt") as f:
    for line in f:
        barcodes.add(line.strip())

inbam = pysam.AlignmentFile("possorted_genome_bam.bam", "rb")
outbam = pysam.AlignmentFile("subset.bam", "wb", template=inbam)

for read in inbam:
    if read.has_tag("CB") and read.get_tag("CB") in barcodes:
        outbam.write(read)

inbam.close()
outbam.close()
pysam.sort("-o", "subset.sorted.bam", "subset.bam")
pysam.index("subset.sorted.bam")
```

### Loading Data in R

#### Seurat

```r
library(Seurat)

# From MEX directory
mat <- Read10X(data.dir = "sample_01/outs/filtered_feature_bc_matrix/")
sobj <- CreateSeuratObject(counts = mat, project = "sample_01")

# From HDF5
mat <- Read10X_h5("sample_01/outs/filtered_feature_bc_matrix.h5")
sobj <- CreateSeuratObject(counts = mat)

# For multi-modal data (e.g., Gene Expression + Antibody Capture),
# Read10X returns a named list of matrices:
data_list <- Read10X(data.dir = "sample_01/outs/filtered_feature_bc_matrix/")
# data_list[["Gene Expression"]]
# data_list[["Antibody Capture"]]
sobj <- CreateSeuratObject(counts = data_list[["Gene Expression"]])
sobj[["ADT"]] <- CreateAssayObject(counts = data_list[["Antibody Capture"]])
```

#### DropletUtils

```r
library(DropletUtils)

# From MEX directory - returns a SingleCellExperiment
sce <- read10xCounts("sample_01/outs/filtered_feature_bc_matrix/")

# From HDF5
sce <- read10xCounts("sample_01/outs/filtered_feature_bc_matrix.h5")

# From raw matrix for custom cell calling with emptyDrops
sce_raw <- read10xCounts("sample_01/outs/raw_feature_bc_matrix/")
e_out <- emptyDrops(counts(sce_raw))
is_cell <- e_out$FDR <= 0.01
sce_filtered <- sce_raw[, which(is_cell)]
```

### Loading Data in Python

#### Scanpy

```python
import scanpy as sc

# From MEX directory
adata = sc.read_10x_mtx(
    "sample_01/outs/filtered_feature_bc_matrix/",
    var_names="gene_symbols",  # use "gene_ids" for Ensembl IDs
    cache=True
)

# From HDF5
adata = sc.read_10x_h5("sample_01/outs/filtered_feature_bc_matrix.h5")

# From raw matrix for custom cell calling
adata_raw = sc.read_10x_mtx("sample_01/outs/raw_feature_bc_matrix/", var_names="gene_symbols")
```

### Cell Ranger Commands

#### cellranger count

Aligns FASTQ reads to a reference genome and generates the feature-barcode matrix for a single library.

```bash
cellranger count \
  --id=sample_01 \
  --transcriptome=/path/to/refdata-gex-GRCh38-2024-A \
  --fastqs=/path/to/fastqs/ \
  --sample=Sample01 \
  --expect-cells=5000 \
  --localcores=16 \
  --localmem=64
```

Key parameters:
- `--id`: A unique run ID; Cell Ranger creates a directory with this name.
- `--transcriptome`: Path to the Cell Ranger-compatible reference (built with `cellranger mkref`).
- `--fastqs`: Path to the directory containing FASTQ files.
- `--sample`: Sample name prefix in the FASTQ filenames (the part before `_S`).
- `--expect-cells`: Expected number of recovered cells (default 3000). Affects the knee-point algorithm.
- `--include-introns`: Included by default in Cell Ranger v7+. Use `--include-introns=false` to exclude intronic reads (useful for comparing with older runs).

#### cellranger aggr

Aggregates multiple `cellranger count` runs, normalizing by mapped read depth across libraries.

```bash
# First create a CSV file listing the runs:
# aggregation.csv:
# sample_id,molecule_h5
# sample_01,/path/to/sample_01/outs/molecule_info.h5
# sample_02,/path/to/sample_02/outs/molecule_info.h5

cellranger aggr \
  --id=aggregated \
  --csv=aggregation.csv \
  --normalize=mapped
```

The `--normalize=mapped` option downsamples reads so each sample has the same effective sequencing depth. Barcode suffixes (`-1`, `-2`, etc.) distinguish cells from different input samples.

#### cellranger multi

Handles multi-library experiments (e.g., Gene Expression + Feature Barcode + VDJ) from a single GEM well, configured via a multi config CSV.

```bash
cellranger multi \
  --id=multi_run \
  --csv=multi_config.csv \
  --localcores=16 \
  --localmem=64
```

Example `multi_config.csv`:

```
[gene-expression]
reference,/path/to/refdata-gex-GRCh38-2024-A
expect-cells,5000

[vdj]
reference,/path/to/refdata-cellranger-vdj-GRCh38-alts-ensembl-7.1.0

[libraries]
fastq_id,fastqs,feature_types
GEX_sample,/path/to/gex_fastqs,Gene Expression
VDJ_sample,/path/to/vdj_fastqs,VDJ-T

[samples]
sample_id,description
mysample,My experiment
```

### STARsolo as a Cell Ranger Alternative

STARsolo is a module within the STAR aligner that replicates Cell Ranger's cell barcode/UMI processing. It is open-source, generally faster, and produces highly concordant results.

#### Basic STARsolo command for 10x Chromium v3

```bash
STAR \
  --soloType CB_UMI_Simple \
  --soloCBwhitelist /path/to/3M-february-2018.txt \
  --genomeDir /path/to/star_index \
  --readFilesIn read2.fastq.gz read1.fastq.gz \
  --readFilesCommand zcat \
  --soloCBstart 1 --soloCBlen 16 \
  --soloUMIstart 17 --soloUMIlen 12 \
  --outSAMtype BAM SortedByCoordinate \
  --outSAMattributes NH HI nM AS CR UR CB UB GX GN sS sQ sM \
  --runThreadN 16 \
  --outFileNamePrefix sample_01_
```

Key STARsolo parameters:
- `--soloType CB_UMI_Simple`: Standard 10x Chromium protocol (barcode + UMI on Read 1).
- `--soloCBwhitelist`: Path to the barcode whitelist file (see Barcode Whitelists below).
- `--readFilesIn`: **Read 2 (cDNA) first, then Read 1 (barcode+UMI)**. This is the opposite of what you might expect.
- `--soloCBstart`, `--soloCBlen`: Cell barcode starts at position 1, length 16 bp.
- `--soloUMIstart`, `--soloUMIlen`: UMI starts at position 17; length is 12 bp for v3 chemistry, 10 bp for v2.
- `--soloCellFilter EmptyDrops_CR`: Mimics Cell Ranger's cell calling algorithm.
- `--soloFeatures Gene GeneFull`: `Gene` counts exonic reads only; `GeneFull` counts exonic + intronic (equivalent to Cell Ranger v7+ default).
- `--soloMultiMappers EM`: Handles multi-mapped reads with an EM algorithm (closer to Cell Ranger behavior).

STARsolo outputs a MEX-format matrix in the `Solo.out/` directory that can be loaded with the same R/Python functions used for Cell Ranger output.

### Barcode Whitelist Locations

10x Genomics provides barcode whitelists that define the set of valid barcodes for each chemistry version. These are needed by STARsolo and other third-party tools.

| Chemistry | Whitelist file | Barcode length | UMI length |
|-----------|---------------|----------------|------------|
| Chromium v2 (Single Cell 3') | `737K-august-2016.txt` | 16 bp | 10 bp |
| Chromium v3 / v3.1 (Single Cell 3') | `3M-february-2018.txt` | 16 bp | 12 bp |
| Chromium v2 (Single Cell 5') | `737K-august-2016.txt` | 16 bp | 10 bp |

Where to find them:

```bash
# Inside the Cell Ranger installation
ls /path/to/cellranger-x.y.z/lib/python/cellranger/barcodes/

# Common files:
# 3M-february-2018.txt.gz   (v3/v3.1 - ~3 million barcodes)
# 737K-august-2016.txt       (v2 - ~737K barcodes)

# Decompress if needed (STARsolo requires uncompressed)
gunzip -k 3M-february-2018.txt.gz

# You can also download them from the 10x GitHub:
# https://github.com/10XGenomics/cellranger/tree/master/lib/python/cellranger/barcodes
```

### Doublet Detection Approaches

Doublets occur when two cells are captured in the same droplet and share a barcode. The expected doublet rate scales with the number of loaded cells (roughly 0.8% per 1000 cells loaded).

#### In R

```r
# scDblFinder (Bioconductor) - fast and well-benchmarked
library(scDblFinder)
sce <- scDblFinder(sce)
# Results in colData(sce)$scDblFinder.class ("singlet" or "doublet")
# and colData(sce)$scDblFinder.score

# DoubletFinder (for Seurat objects)
library(DoubletFinder)
# Requires pre-processed Seurat object (normalized, PCA, UMAP)
sweep_res <- paramSweep(sobj, PCs = 1:20, sct = FALSE)
sweep_stats <- summarizeSweep(sweep_res, GT = FALSE)
bcmvn <- find.pK(sweep_stats)
# Choose optimal pK, then:
nExp <- round(0.04 * nrow(sobj@meta.data))  # assuming ~4% doublet rate
sobj <- doubletFinder(sobj, PCs = 1:20, pN = 0.25, pK = 0.09, nExp = nExp)
```

#### In Python

```python
# Scrublet
import scrublet as scr
scrub = scr.Scrublet(adata.X, expected_doublet_rate=0.06)
doublet_scores, predicted_doublets = scrub.scrub_doublets()
adata.obs["doublet_score"] = doublet_scores
adata.obs["predicted_doublet"] = predicted_doublets

# scvi-tools (SOLO)
# Train a scVI model first, then use SOLO for doublet detection
import scvi
scvi.model.SCVI.setup_anndata(adata)
vae = scvi.model.SCVI(adata)
vae.train()
solo = scvi.external.SOLO.from_scvi_model(vae)
solo.train()
df = solo.predict()
```

## Key Concepts

### UMI Deduplication

Each mRNA molecule captured in a 10x droplet is tagged with a random UMI (unique molecular identifier). During PCR amplification, the same molecule produces many duplicate reads. UMI deduplication collapses all reads that share the same cell barcode, UMI, and gene assignment into a single count. This is what converts raw read counts into a digital gene expression matrix and removes PCR amplification bias.

Cell Ranger performs UMI deduplication accounting for:
- Sequencing errors in UMIs (Hamming distance 1 collapsing via directional adjacency)
- Multi-mapped reads (by default, only confidently mapped reads contribute)

### Cell Barcode Correction

The raw barcode sequenced from Read 1 (`CR:Z` tag) may contain sequencing errors. Cell Ranger corrects barcodes by:
1. Comparing each observed barcode to the whitelist.
2. If the barcode is on the whitelist, it is accepted as-is.
3. If the barcode is within Hamming distance 1 of exactly one whitelist barcode (and the base quality at the mismatched position is low), it is corrected to that whitelist barcode.
4. Barcodes that cannot be unambiguously corrected are discarded (no `CB:Z` tag in the BAM).

The corrected barcode appears in the `CB:Z` tag. Reads lacking a `CB:Z` tag failed barcode correction and are not counted in the matrix.

### Knee Plot and Empty Droplet Filtering

Cell Ranger uses a knee-point algorithm to distinguish cell-containing droplets from empty droplets:

1. All barcodes are ranked by total UMI counts in descending order.
2. The "knee" is the point where UMI counts drop sharply -- barcodes above this threshold are likely cells.
3. Cell Ranger v3+ uses an improved algorithm (EmptyDrops-like) that can recover cells with lower RNA content that fall below the simple knee point.

You can inspect this in the `web_summary.html` barcode rank plot.

To perform your own cell calling using the raw matrix:

```r
library(DropletUtils)
sce_raw <- read10xCounts("sample_01/outs/raw_feature_bc_matrix/")
set.seed(42)
e_out <- emptyDrops(counts(sce_raw), lower = 100, niters = 10000)
is_cell <- e_out$FDR <= 0.01
table(is_cell, useNA = "always")
```

## Common Pitfalls

### Barcode Suffix `-1`

Cell Ranger appends `-1` to every barcode (e.g., `AAACCTGAGAAGGCCT-1`). The suffix is a sample/GEM-well index used by `cellranger aggr` to distinguish cells from different samples (sample 1 gets `-1`, sample 2 gets `-2`, etc.). When matching barcodes across tools or files, ensure the suffix is consistent. Some tools strip the suffix; others require it.

```bash
# To strip the suffix
sed 's/-[0-9]*$//' barcodes.tsv.gz > barcodes_nosuffix.txt

# When filtering BAMs, always use the suffixed form since CB:Z tags include it
```

### Filtered vs. Raw Matrix

- **filtered_feature_bc_matrix**: Contains only barcodes Cell Ranger called as cells. Use this for standard analyses.
- **raw_feature_bc_matrix**: Contains ALL observed barcodes (typically hundreds of thousands to millions). Use this only when you want to apply your own cell-calling algorithm (e.g., `emptyDrops()`), inspect ambient RNA profiles, or perform decontamination (e.g., SoupX, CellBender).

Loading the raw matrix when you intend to use the filtered one wastes memory and will include noise from empty droplets.

### Memory Requirements

10x data processing is memory-intensive:

| Step | Typical RAM |
|------|------------|
| `cellranger count` (human/mouse genome) | 32--64 GB |
| STARsolo (human/mouse genome) | 32--40 GB |
| Loading a filtered matrix (5,000--10,000 cells) | 1--4 GB |
| Loading a raw matrix (~6M barcodes) | 10--30 GB |
| Seurat standard workflow (10,000 cells) | 2--8 GB |
| Seurat standard workflow (100,000+ cells) | 32--64 GB+ |

Tips to manage memory:
- Use HDF5-backed objects (e.g., `HDF5Array` in R, backed mode in AnnData) for large datasets.
- Downsample or subset early if exploring.
- For `cellranger count`, set `--localmem` to avoid exceeding available RAM.
- STARsolo genome index generation (`--runMode genomeGenerate`) requires substantial RAM; use `--genomeSAsparseD 3` to reduce memory at the cost of speed.

### FASTQ File Naming Convention

Cell Ranger expects FASTQ files to follow the Illumina naming convention:

```
[SampleName]_S[Number]_L[Lane]_[ReadType]_001.fastq.gz
```

Where `ReadType` is:
- `R1`: Read 1 (contains barcode + UMI for 10x)
- `R2`: Read 2 (contains cDNA insert)
- `I1`: Index read (sample index)

If your files do not follow this convention, Cell Ranger will not find them. Use `cellranger mkfastq` to generate properly named FASTQs from BCL files, or rename files to match the expected pattern.

### Genome Reference Version Mismatch

Always ensure that downstream analyses use the same genome reference as the one used for alignment. Mixing references (e.g., Ensembl gene IDs from one release with a Cell Ranger reference from another) leads to mismatched gene IDs and dropped features. Cell Ranger references use a specific filtered GTF; the gene set may differ from standard Ensembl or GENCODE releases.

### Intronic Reads

Cell Ranger v7+ counts intronic reads by default (`--include-introns=true`). This increases sensitivity (especially for nuclei or pre-mRNA) but changes total UMI counts compared to v6 and earlier. When comparing datasets processed with different Cell Ranger versions, ensure consistent intron handling. Use `--include-introns=false` to replicate v6 behavior.
