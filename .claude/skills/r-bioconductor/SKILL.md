---
name: r-bioconductor
description: R and Bioconductor genomics toolkit. Analyze single-cell RNA-seq with SingleCellExperiment/Seurat, differential expression with DESeq2/edgeR, genomic ranges with GenomicRanges, and visualization with ggplot2 for publication-quality figures.
license: MIT license
metadata:
    skill-author: VFranke
---

# R and Bioconductor Genomics Toolkit

## Overview

This skill provides guidance for bioinformatics analysis in R using Bioconductor packages. It covers single-cell RNA-seq workflows, differential gene expression, genomic interval operations, sequence manipulation, enrichment analysis, and publication-quality visualization. The primary R installation is at `/opt/R/4.5/bin/R` (R 4.5).

All code should follow Bioconductor conventions: S4 classes, generic functions, and the SummarizedExperiment data model. Prefer Bioconductor packages over CRAN equivalents when both exist for the same task.

## When to Use

Use this skill when the user needs to:

- Create, manipulate, or analyze **SingleCellExperiment** or **SummarizedExperiment** objects
- Run **differential expression** analysis with DESeq2 or edgeR
- Work with **genomic coordinates** (GRanges, GAlignments) or BAM files
- Perform **enrichment analysis** (GO, KEGG, GSEA) with clusterProfiler or enrichR
- Build **publication-quality figures** with ggplot2 or ComplexHeatmap
- Import/export genomic file formats (BED, BigWig, GTF, GFF) with rtracklayer
- Manipulate **biological sequences** with Biostrings
- Perform single-cell **QC, normalization, and clustering** with scran/scater

## Quick Start Examples

### Creating a SingleCellExperiment from a count matrix

```r
library(SingleCellExperiment)

# counts: genes x cells matrix; coldata: per-cell metadata data.frame
sce <- SingleCellExperiment(
    assays = list(counts = counts_matrix),
    colData = coldata,
    rowData = rowdata
)

# Log-normalize
library(scuttle)
sce <- logNormCounts(sce)

# Access
counts(sce)          # raw counts
logcounts(sce)       # log-normalized
colData(sce)         # cell metadata
reducedDim(sce, "PCA")
```

### DESeq2 differential expression (bulk RNA-seq)

```r
library(DESeq2)

dds <- DESeqDataSetFromMatrix(
    countData = count_matrix,   # genes x samples, raw integer counts
    colData   = sample_info,    # data.frame with sample metadata
    design    = ~ condition     # formula referencing colData columns
)
dds <- DESeq(dds)
res <- results(dds, contrast = c("condition", "treated", "control"))
res <- res[order(res$padj), ]
summary(res)
```

### Genomic ranges operations

```r
library(GenomicRanges)

gr <- GRanges(
    seqnames = c("chr1", "chr1", "chr2"),
    ranges   = IRanges(start = c(100, 200, 150), width = 50),
    strand   = c("+", "-", "+"),
    score    = c(10, 20, 15)
)

# Find overlaps between two GRanges
hits <- findOverlaps(query_gr, subject_gr)

# Subset to promoters (2kb upstream of TSS)
promoters <- promoters(gene_gr, upstream = 2000, downstream = 200)
```

### ggplot2 publication figure

```r
library(ggplot2)

ggplot(df, aes(x = log2FoldChange, y = -log10(padj), colour = significant)) +
    geom_point(size = 0.8, alpha = 0.6) +
    scale_colour_manual(values = c("grey60", "firebrick")) +
    geom_vline(xintercept = c(-1, 1), linetype = "dashed") +
    geom_hline(yintercept = -log10(0.05), linetype = "dashed") +
    labs(x = "log2 Fold Change", y = "-log10 adjusted p-value", title = "Volcano Plot") +
    theme_bw(base_size = 14) +
    theme(legend.position = "none")
```

## Core Capabilities

### Single-Cell RNA-seq Workflows

#### QC and Filtering (scater / scuttle)

```r
library(scater)
library(scuttle)

# Compute per-cell QC metrics
is_mito <- grepl("^MT-", rowData(sce)$Symbol)
sce <- addPerCellQCMetrics(sce, subsets = list(mito = is_mito))

# Filter cells: adaptive thresholds using median absolute deviations
qc_filters <- perCellQCFilters(
    colData(sce),
    sub.fields = "subsets_mito_percent"
)
sce <- sce[, !qc_filters$discard]
```

#### Normalization and Feature Selection (scran)

```r
library(scran)

# Deconvolution-based normalization (preferred for scRNA-seq)
clusters <- quickCluster(sce)
sce <- computeSumFactors(sce, clusters = clusters)
sce <- logNormCounts(sce)

# Model gene variance and select highly variable genes
dec <- modelGeneVar(sce)
hvgs <- getTopHVGs(dec, n = 2000)
```

#### Dimensionality Reduction and Clustering

```r
library(scran)
library(scater)

# PCA on HVGs
sce <- runPCA(sce, subset_row = hvgs)

# UMAP from PCA
sce <- runUMAP(sce, dimred = "PCA")

# Graph-based clustering
g <- buildSNNGraph(sce, use.dimred = "PCA", k = 20)
clusters <- igraph::cluster_walktrap(g)$membership
colData(sce)$cluster <- factor(clusters)
```

#### Marker Gene Detection

```r
# Find markers for each cluster vs all others
markers <- findMarkers(sce, groups = sce$cluster, test.type = "t")

# markers is a list of DataFrames, one per cluster
# Columns: Top, p.value, FDR, summary.logFC, logFC.<cluster>
top_markers <- markers[["1"]]  # markers for cluster 1
top_markers <- top_markers[top_markers$FDR < 0.05, ]
```

#### Plotting Single-Cell Data

```r
# UMAP colored by cluster
plotUMAP(sce, colour_by = "cluster")

# Expression of a gene on UMAP
plotUMAP(sce, colour_by = "Gapdh")

# Violin plot of gene expression per cluster
plotExpression(sce, features = c("Gapdh", "Actb"), x = "cluster")
```

### Differential Expression

#### DESeq2 (Recommended for most bulk RNA-seq)

```r
library(DESeq2)

# Build object from count matrix
dds <- DESeqDataSetFromMatrix(
    countData = count_matrix,
    colData   = sample_info,
    design    = ~ batch + condition   # batch as covariate
)

# Pre-filtering: remove low-count genes
keep <- rowSums(counts(dds) >= 10) >= 3
dds <- dds[keep, ]

# Run pipeline
dds <- DESeq(dds)

# Extract results with specific contrast
res <- results(dds, contrast = c("condition", "treated", "control"),
               alpha = 0.05)

# Shrink log2 fold changes for visualization (apeglm is preferred)
res_shrunk <- lfcShrink(dds, coef = "condition_treated_vs_control",
                         type = "apeglm")

# Variance-stabilized counts for PCA/heatmaps
vsd <- vst(dds, blind = FALSE)
plotPCA(vsd, intgroup = "condition")
```

#### edgeR (Alternative, especially for small samples or complex designs)

```r
library(edgeR)

# Build DGEList
dge <- DGEList(counts = count_matrix, group = sample_info$condition)

# Filter low-expression genes
keep <- filterByExpr(dge)
dge <- dge[keep, , keep.lib.sizes = FALSE]

# Normalize (TMM)
dge <- calcNormFactors(dge)

# Design matrix
design <- model.matrix(~ 0 + condition, data = sample_info)

# Estimate dispersions
dge <- estimateDisp(dge, design)

# Quasi-likelihood F-test (recommended)
fit <- glmQLFit(dge, design)
contrast <- makeContrasts(conditiontreated - conditioncontrol, levels = design)
qlf <- glmQLFTest(fit, contrast = contrast)
topTags(qlf, n = 20)
```

#### Pseudobulk DE from Single-Cell Data

```r
library(scuttle)
library(DESeq2)

# Aggregate counts by sample + cluster
agg <- aggregateAcrossCells(sce,
    ids = colData(sce)[, c("sample_id", "cluster")]
)

# For a specific cluster, run DESeq2
sub <- agg[, agg$cluster == "1"]
dds <- DESeqDataSetFromMatrix(
    countData = counts(sub),
    colData   = colData(sub),
    design    = ~ condition
)
dds <- DESeq(dds)
res <- results(dds)
```

### Genomic Ranges and BAM Operations

#### Working with GRanges

```r
library(GenomicRanges)

# Create GRanges
gr <- GRanges(
    seqnames = Rle(c("chr1", "chr2"), c(3, 2)),
    ranges   = IRanges(start = c(1, 100, 200, 50, 80), width = 50),
    strand   = c("+", "+", "-", "*", "-"),
    gene_id  = paste0("gene", 1:5)
)

# Accessors
seqnames(gr)
start(gr)
end(gr)
width(gr)
strand(gr)
mcols(gr)$gene_id

# Intra-range operations (operate on each range individually)
flank(gr, width = 500, start = TRUE)   # 500bp upstream flanks
resize(gr, width = 1, fix = "start")   # TSS (single-base)
shift(gr, shift = 100)                 # shift all ranges 100bp
narrow(gr, start = 1, width = 10)      # trim each range

# Inter-range operations (operate across ranges)
reduce(gr)                             # merge overlapping ranges
disjoin(gr)                            # non-overlapping pieces
gaps(gr)                               # gaps between ranges
coverage(gr)                           # per-base coverage as Rle

# Set operations
intersect(gr1, gr2)
union(gr1, gr2)
setdiff(gr1, gr2)

# Overlaps
hits <- findOverlaps(query, subject, maxgap = 0, minoverlap = 1)
queryHits(hits)
subjectHits(hits)
overlaps_any <- overlapsAny(query, subject)
query_in_subject <- subsetByOverlaps(query, subject)
query_outside    <- subsetByOverlaps(query, subject, invert = TRUE)
```

#### Reading BAM Files

```r
library(GenomicAlignments)
library(Rsamtools)

# Read all alignments (memory intensive for large BAMs)
bam_file <- BamFile("sample.bam", yieldSize = 1e6)

# Read with specific parameters
param <- ScanBamParam(
    which = GRanges("chr1", IRanges(1, 1e6)),   # region filter
    what  = c("mapq", "flag"),                    # fields to load
    flag  = scanBamFlag(isUnmappedQuery = FALSE,
                        isDuplicate = FALSE)
)
reads <- readGAlignments(bam_file, param = param)

# Count reads in genomic features
library(GenomicFeatures)
txdb <- makeTxDbFromGFF("genes.gtf")
exons_by_gene <- exonsBy(txdb, by = "gene")
counts <- summarizeOverlaps(
    features = exons_by_gene,
    reads    = bam_files,       # BamFileList
    mode     = "Union",
    singleEnd = FALSE,
    fragments = TRUE
)
# counts is a RangedSummarizedExperiment
assay(counts)   # count matrix
```

#### Import/Export with rtracklayer

```r
library(rtracklayer)

# Import BED / GTF / BigWig
bed <- import("regions.bed")                       # returns GRanges
gtf <- import("genes.gtf")                         # returns GRanges with metadata
bw  <- import("signal.bw", which = region_gr)      # BigWig for specific regions

# Export
export(gr, "output.bed", format = "BED")
export(gr, "output.gtf", format = "GTF")
export(coverage_gr, "signal.bw", format = "BigWig")

# Liftover between genome assemblies
chain <- import.chain("hg19ToHg38.over.chain")
gr_hg38 <- liftOver(gr_hg19, chain)   # returns GRangesList
gr_hg38 <- unlist(gr_hg38)
```

### Sequence Operations with Biostrings

```r
library(Biostrings)
library(BSgenome.Hsapiens.UCSC.hg38)

# Extract sequences for genomic regions
seqs <- getSeq(BSgenome.Hsapiens.UCSC.hg38, gr)

# Pattern matching
vmatchPattern("GATTACA", seqs)

# Compute nucleotide frequencies
letterFrequency(seqs, letters = c("G", "C"), as.prob = TRUE)

# Read/write FASTA
seqs <- readDNAStringSet("sequences.fasta")
writeXStringSet(seqs, "output.fasta")

# Translate DNA to protein
aa <- translate(dna_seqs)
```

### Visualization

#### ggplot2 Common Patterns

```r
library(ggplot2)

# MA plot
ggplot(as.data.frame(res), aes(x = baseMean, y = log2FoldChange,
                                colour = padj < 0.05)) +
    geom_point(size = 0.5, alpha = 0.4) +
    scale_x_log10() +
    scale_colour_manual(values = c("grey50", "red3")) +
    theme_bw(base_size = 14)

# Boxplot of expression across conditions
ggplot(expr_long, aes(x = condition, y = expression, fill = condition)) +
    geom_boxplot(outlier.size = 0.5) +
    facet_wrap(~ gene, scales = "free_y") +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))

# Barplot of cell-type proportions
ggplot(prop_df, aes(x = sample, y = proportion, fill = cell_type)) +
    geom_col(position = "fill") +
    scale_y_continuous(labels = scales::percent) +
    theme_minimal(base_size = 14) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))

# Saving figures
ggsave("figure.pdf", width = 8, height = 6, dpi = 300)
ggsave("figure.png", width = 8, height = 6, dpi = 300)
```

#### ComplexHeatmap

```r
library(ComplexHeatmap)
library(circlize)

# Expression heatmap of top DE genes
mat <- assay(vsd)[top_gene_ids, ]
mat <- t(scale(t(mat)))  # z-score per gene

col_fun <- colorRamp2(c(-2, 0, 2), c("navy", "white", "firebrick"))

ha <- HeatmapAnnotation(
    condition = colData(vsd)$condition,
    batch     = colData(vsd)$batch,
    col = list(
        condition = c("control" = "grey70", "treated" = "tomato"),
        batch     = c("A" = "#1b9e77", "B" = "#d95f02")
    )
)

Heatmap(
    mat,
    name = "z-score",
    col  = col_fun,
    top_annotation = ha,
    show_row_names = TRUE,
    row_names_gp   = gpar(fontsize = 8),
    cluster_columns = TRUE,
    cluster_rows    = TRUE,
    column_title    = "Top DE Genes"
)
```

### Enrichment Analysis

#### clusterProfiler for GO / KEGG

```r
library(clusterProfiler)
library(org.Hs.eg.db)

# Gene list: named vector of log2FC, names are Entrez IDs
gene_list <- res$log2FoldChange
names(gene_list) <- mapIds(org.Hs.eg.db,
                           keys = rownames(res),
                           column = "ENTREZID",
                           keytype = "ENSEMBL",
                           multiVals = "first")
gene_list <- sort(gene_list, decreasing = TRUE)
gene_list <- gene_list[!is.na(names(gene_list))]

# Over-representation analysis (ORA) with significant genes
sig_genes <- names(gene_list)[abs(gene_list) > 1]
ego <- enrichGO(
    gene     = sig_genes,
    OrgDb    = org.Hs.eg.db,
    ont      = "BP",
    pAdjustMethod = "BH",
    pvalueCutoff  = 0.05,
    readable = TRUE
)
dotplot(ego, showCategory = 20)

# Gene Set Enrichment Analysis (GSEA) with full ranked list
gsea_res <- gseGO(
    geneList = gene_list,
    OrgDb    = org.Hs.eg.db,
    ont      = "BP",
    pvalueCutoff = 0.05
)
ridgeplot(gsea_res, showCategory = 15)

# KEGG pathway enrichment
ekegg <- enrichKEGG(
    gene     = sig_genes,
    organism = "hsa",
    pvalueCutoff = 0.05
)
```

#### enrichR (Broad library access)

```r
library(enrichR)

setEnrichR("Enrichr")  # or "speedrichr" for newer API
dbs <- listEnrichrDbs()

# Run enrichment with gene symbols
results <- enrichr(gene_symbols, databases = c(
    "GO_Biological_Process_2023",
    "KEGG_2021_Human",
    "MSigDB_Hallmark_2020"
))

# Access results
go_results <- results[["GO_Biological_Process_2023"]]
go_results <- go_results[go_results$Adjusted.P.value < 0.05, ]
```

## Key Concepts

### SummarizedExperiment Hierarchy

The Bioconductor data model is built on a class hierarchy:

```
SummarizedExperiment          # Base class: assays + rowData + colData
  |-- RangedSummarizedExperiment   # Adds rowRanges (GRanges per feature)
        |-- SingleCellExperiment   # Adds reducedDims, altExps, colPairs
        |-- DESeqDataSet           # DESeq2-specific (adds design formula)
```

**Shared interface for all SE-family objects:**

| Accessor         | Returns                        | Description                         |
|------------------|--------------------------------|-------------------------------------|
| `assay(x)`       | matrix                         | Primary assay (e.g., counts)        |
| `assays(x)`      | list of matrices               | All assays (counts, logcounts, etc) |
| `colData(x)`     | DataFrame                      | Sample/cell metadata (columns)      |
| `rowData(x)`     | DataFrame                      | Feature metadata (rows)             |
| `rowRanges(x)`   | GRanges / GRangesList          | Genomic coordinates per feature     |
| `metadata(x)`    | list                           | Arbitrary experiment-level metadata |

**Rules:**
- Rows are features (genes), columns are samples/cells.
- Subsetting works like a matrix: `se[rows, columns]`.
- Always use accessor functions instead of `@` slot access.

### GRanges Coordinate System

- Bioconductor uses **1-based, closed intervals**: a range with start=1, end=10 includes positions 1 through 10 (10 bases).
- BED format is **0-based, half-open**: the same region is [0, 10). `rtracklayer::import` handles this conversion automatically.
- Strand can be `"+"`, `"-"`, or `"*"` (unstranded).
- `seqinfo()` stores chromosome lengths and genome assembly; set it to enable boundary checking.

```r
# Setting seqinfo for proper coordinate validation
seqinfo(gr) <- Seqinfo(genome = "hg38")

# Or manually
seqlevelsStyle(gr) <- "UCSC"  # chr1, chr2 ...
seqlevelsStyle(gr) <- "Ensembl"  # 1, 2, ...
```

### Formula Interface for DE Models

DESeq2 and edgeR use R formulas to specify the statistical model:

```r
# Simple two-group comparison
design = ~ condition

# Controlling for batch effects
design = ~ batch + condition

# Interaction model
design = ~ genotype + treatment + genotype:treatment

# The last term in the formula is the variable of interest for DESeq2.
# For edgeR with model.matrix(~ 0 + ...), use contrasts explicitly.
```

**Important:** The reference level of a factor determines the direction of fold change. Set it explicitly:

```r
sample_info$condition <- relevel(factor(sample_info$condition), ref = "control")
```

## Common Pitfalls

### 1. Feeding normalized counts to DESeq2 or edgeR

DESeq2 and edgeR require **raw integer counts**. They perform their own normalization internally. Passing TPM, FPKM, or log-transformed values will produce incorrect results.

```r
# WRONG
dds <- DESeqDataSetFromMatrix(countData = tpm_matrix, ...)

# CORRECT
dds <- DESeqDataSetFromMatrix(countData = raw_counts, ...)
```

### 2. Not setting the reference level before DE analysis

If the reference level is not explicitly set, R uses alphabetical order. This can flip the direction of fold changes.

```r
# May give "treated vs control" or "control vs treated" depending on sorting
# Always set explicitly:
colData(dds)$condition <- relevel(factor(colData(dds)$condition), ref = "control")
```

### 3. Forgetting to filter low-count genes

Low-count genes add noise and inflate the multiple testing burden. Always filter before DE analysis.

```r
# DESeq2
keep <- rowSums(counts(dds) >= 10) >= min_samples
dds <- dds[keep, ]

# edgeR
keep <- filterByExpr(dge, design)
dge <- dge[keep, , keep.lib.sizes = FALSE]
```

### 4. Using raw counts for PCA or heatmaps

Raw counts are heteroscedastic (variance depends on the mean). Use variance-stabilized or log-normalized values for distance-based analyses.

```r
# DESeq2: variance-stabilizing transformation
vsd <- vst(dds, blind = FALSE)

# Or regularized log (slower but better for small sample sizes)
rld <- rlog(dds, blind = FALSE)

# SingleCellExperiment: logNormCounts
sce <- logNormCounts(sce)
```

### 5. Coordinate system confusion (BED vs GRanges)

BED uses 0-based, half-open coordinates. GRanges uses 1-based, closed. Let `rtracklayer::import()` and `rtracklayer::export()` handle conversions. Do not manually add or subtract 1 from coordinates read through rtracklayer.

### 6. Running cell-level DE on single-cell data

Treating each cell as a replicate inflates statistical significance because cells from the same sample are not independent. Use pseudobulk aggregation instead.

```r
# WRONG: thousands of "replicates" from the same few samples
# FindMarkers(seurat_obj, ident.1 = "treated", ident.2 = "control")

# CORRECT: pseudobulk by sample, then use DESeq2/edgeR
agg <- aggregateAcrossCells(sce, ids = colData(sce)[, c("sample_id", "cluster")])
```

### 7. Not keeping seqlevels consistent

Mixing UCSC (`chr1`) and Ensembl (`1`) chromosome naming causes silent failures in overlap operations.

```r
# Check and convert
seqlevelsStyle(gr)
seqlevelsStyle(gr) <- "UCSC"

# Keep only standard chromosomes
gr <- keepStandardChromosomes(gr, pruning.mode = "coarse")
```

### 8. Memory issues with large SingleCellExperiment objects

For large datasets, use sparse matrices and on-disk backends:

```r
# Ensure counts are sparse
library(Matrix)
counts(sce) <- as(counts(sce), "dgCMatrix")

# For very large data, use HDF5 backend
library(HDF5Array)
sce <- saveHDF5SummarizedExperiment(sce, dir = "sce_h5")
sce <- loadHDF5SummarizedExperiment("sce_h5")
```

### 9. Plotting too many points in ggplot2

For scRNA-seq UMAPs or volcano plots with hundreds of thousands of points, use `scattermore` or rasterization to keep file sizes manageable.

```r
library(scattermore)
ggplot(df, aes(UMAP1, UMAP2, colour = cluster)) +
    geom_scattermore(pointsize = 1, pixels = c(1024, 1024)) +
    theme_bw()

# Or rasterize the geom layer with ggrastr
library(ggrastr)
ggplot(df, aes(UMAP1, UMAP2, colour = cluster)) +
    rasterise(geom_point(size = 0.3), dpi = 300) +
    theme_bw()
```

### 10. Ignoring gene ID mapping issues

Gene IDs from different sources (Ensembl, NCBI, HGNC symbols) may not match. Always verify mappings and handle many-to-one or missing mappings explicitly.

```r
library(org.Hs.eg.db)

# Map Ensembl to Symbol, keeping first match for duplicates
symbols <- mapIds(org.Hs.eg.db,
                  keys    = ensembl_ids,
                  column  = "SYMBOL",
                  keytype = "ENSEMBL",
                  multiVals = "first")

# Check how many failed to map
sum(is.na(symbols))
```
