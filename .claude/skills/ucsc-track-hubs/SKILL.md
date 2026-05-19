---
name: ucsc-track-hubs
description: UCSC Genome Browser track hubs. Build bigWig/bigBed track lines, create track hub directories, configure composite and multiWig tracks, and generate public/private browser links for data sharing.
license: MIT license
metadata:
    skill-author: VFranke
---

# UCSC Genome Browser Track Hubs

## Overview

This skill covers creating and managing UCSC Genome Browser track hubs and track lines for visualizing and sharing genomic data. Track hubs are web-accessible directories containing configuration files that tell the UCSC browser where to find and how to display binary indexed genomic data files (bigWig, bigBed, BAM, VCF). They are the standard mechanism for hosting custom tracks outside of UCSC, enabling data sharing with collaborators and the public.

**Core capabilities:**
- Generate track lines for quick visualization of bigWig, bigBed, BAM, and VCF files
- Build complete track hub directory structures (hub.txt, genomes.txt, trackDb.txt)
- Configure composite tracks, multiWig overlays, and superTracks for organizing related data
- Convert common genomics formats (bedGraph, BED, BAM) to binary indexed formats (bigWig, bigBed)
- Generate browser session links for data sharing via a static web server (e.g., bimsbstatic.mdc-berlin.de)

## When to Use This Skill

Use this skill when:

- **Creating track lines**: "Make a bigWig track line for my ChIP-seq coverage", "I need a track URL for the browser"
- **Building track hubs**: "Set up a track hub for my project", "Create hub.txt and trackDb.txt"
- **Organizing tracks**: "Group my replicates as composite tracks", "Overlay my bigWig files in a multiWig"
- **Format conversion**: "Convert bedGraph to bigWig", "Make a bigBed from my BED file"
- **Sharing data**: "Generate a browser link for my collaborator", "Host tracks on bimsbstatic"
- **Display configuration**: "Change track colors", "Set axis scaling", "Configure track visibility"

## Quick Start: Simple bigWig Track Line

The fastest way to view a hosted bigWig file in the UCSC browser is with a track line. If the file is already in bigWig format and accessible via HTTP/HTTPS:

```
track type=bigWig name="H3K27ac_rep1" bigDataUrl=https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_rep1.bw
```

To load this in the browser:

1. Go to https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38
2. Click "My Data" -> "Custom Tracks"
3. Paste the track line into the text box and click "Submit"

Or construct a direct URL:

```
https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&hgct_customText=track%20type=bigWig%20name=%22H3K27ac_rep1%22%20bigDataUrl=https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_rep1.bw
```

## Core Capabilities

### Track Line Format

Track lines are single-line declarations that tell the UCSC browser how to fetch and display a remote data file. The basic format is:

```
track type=bigWig name="sample_name" bigDataUrl=https://server/path/to/file.bw
```

**bigWig track line (signal/coverage):**
```
track type=bigWig name="H3K27ac WT" description="H3K27ac ChIP-seq wild type" bigDataUrl=https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_WT.bw color=0,0,178 visibility=full maxHeightPixels=50:30:10 viewLimits=0:20 autoScale=off
```

**bigBed track line (intervals/peaks):**
```
track type=bigBed name="ATAC peaks" description="ATAC-seq peaks called by MACS2" bigDataUrl=https://bimsbstatic.mdc-berlin.de/ohler/project/atac_peaks.bb color=200,0,0 visibility=pack
```

**BAM track line (alignments):**
```
track type=bam name="RNA-seq reads" bigDataUrl=https://bimsbstatic.mdc-berlin.de/ohler/project/rnaseq.bam
```

**VCF track line (variants):**
```
track type=vcfTabix name="Variants" bigDataUrl=https://bimsbstatic.mdc-berlin.de/ohler/project/variants.vcf.gz
```

**Key parameters for track lines:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `type` | File format | `bigWig`, `bigBed`, `bam`, `vcfTabix` |
| `name` | Short label shown in browser | `"H3K27ac rep1"` |
| `description` | Longer description | `"H3K27ac ChIP-seq replicate 1"` |
| `bigDataUrl` | Full URL to the data file | `https://server/path/file.bw` |
| `color` | RGB color | `0,0,178` (blue) |
| `visibility` | Display mode | `hide`, `dense`, `squish`, `pack`, `full` |
| `viewLimits` | Y-axis range (bigWig) | `0:20` |
| `autoScale` | Auto Y-axis scaling | `on`, `off` |
| `maxHeightPixels` | Track height max:default:min | `100:50:10` |
| `windowingFunction` | Signal aggregation | `mean`, `maximum` |

### Track Types

**bigWig** -- Continuous signal data (coverage, ChIP-seq signal, ATAC-seq signal, RNA-seq coverage). This is the most commonly used track type for displaying genome-wide quantitative data. Binary indexed format derived from bedGraph or wiggle.

**bigBed** -- Interval/region data (peaks, annotations, regulatory elements). Binary indexed version of BED format. Supports BED3 through BED12+ with optional extra fields. Use for MACS2 peak calls, gene annotations, enhancer regions, etc.

**BAM** -- Aligned sequencing reads. Requires an index file (.bam.bai) at the same URL location. The browser renders individual reads or coverage depending on zoom level. Useful for inspecting alignments but very heavy for browsing -- prefer bigWig for signal visualization.

**VCF (vcfTabix)** -- Variant calls. Must be bgzip-compressed and tabix-indexed. The .vcf.gz.tbi index file must be at the same URL. Displays SNPs, indels, and structural variants.

### Track Hub Structure

A track hub is a directory of plain text configuration files served over HTTP/HTTPS. The minimal structure is:

```
myHub/
  hub.txt          # Hub metadata (entry point)
  genomes.txt      # Lists assemblies and their trackDb files
  hg38/
    trackDb.txt    # Track definitions for hg38
```

**hub.txt** -- The entry point. The browser loads this first.
```
hub myProjectHub
shortLabel My Project
longLabel ChIP-seq and ATAC-seq data from My Project
genomesFile genomes.txt
email user@mdc-berlin.de
```

**genomes.txt** -- Maps genome assemblies to their trackDb files.
```
genome hg38
trackDb hg38/trackDb.txt

genome mm10
trackDb mm10/trackDb.txt
```

**trackDb.txt** -- Defines all tracks for a given assembly. This is where the bulk of configuration lives.
```
track H3K27ac_WT
type bigWig
shortLabel H3K27ac WT
longLabel H3K27ac ChIP-seq wild type replicate 1
bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_WT.bw
color 0,0,178
visibility full
maxHeightPixels 100:50:10
viewLimits 0:20
autoScale off

track ATAC_peaks
type bigBed
shortLabel ATAC peaks
longLabel ATAC-seq peaks MACS2 q0.01
bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/atac_peaks.bb
color 200,0,0
visibility pack
```

**Loading a track hub in the browser:**

```
https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&hubUrl=https://bimsbstatic.mdc-berlin.de/ohler/project/hub.txt
```

Or go to "My Data" -> "Track Hubs" -> "My Hubs" tab, paste the hub.txt URL, and click "Add Hub".

### Composite Tracks

Composite tracks group related tracks (e.g., replicates, conditions) into a single collapsible container. Users can toggle individual subtracks on/off.

```
track chipseqComposite
compositeTrack on
shortLabel ChIP-seq
longLabel H3K27ac ChIP-seq all samples
type bigWig
visibility full
maxHeightPixels 100:50:10
autoScale on

    track H3K27ac_WT_rep1
    parent chipseqComposite on
    type bigWig
    shortLabel WT rep1
    longLabel H3K27ac ChIP-seq wild type replicate 1
    bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_WT_rep1.bw
    color 0,0,178

    track H3K27ac_WT_rep2
    parent chipseqComposite on
    type bigWig
    shortLabel WT rep2
    longLabel H3K27ac ChIP-seq wild type replicate 2
    bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_WT_rep2.bw
    color 0,0,178

    track H3K27ac_KO_rep1
    parent chipseqComposite on
    type bigWig
    shortLabel KO rep1
    longLabel H3K27ac ChIP-seq knockout replicate 1
    bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_KO_rep1.bw
    color 178,0,0

    track H3K27ac_KO_rep2
    parent chipseqComposite on
    type bigWig
    shortLabel KO rep2
    longLabel H3K27ac ChIP-seq knockout replicate 2
    bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_KO_rep2.bw
    color 178,0,0
```

Note: Subtracks are indented with spaces (convention, not strictly required). The `parent trackName on` setting means the subtrack is visible by default; use `off` to hide it initially.

### MultiWig Overlay

MultiWig overlays display multiple bigWig signals in the same vertical space, making direct comparison easy. This is implemented as a composite track with a special `container multiWig` declaration.

```
track H3K27ac_overlay
container multiWig
shortLabel H3K27ac overlay
longLabel H3K27ac ChIP-seq WT vs KO overlay
type bigWig
visibility full
maxHeightPixels 100:60:10
viewLimits 0:25
autoScale off
aggregate transparentOverlay
showSubtrackColorOnUi on

    track H3K27ac_WT_overlay
    parent H3K27ac_overlay
    type bigWig
    shortLabel WT
    bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_WT.bw
    color 0,0,178

    track H3K27ac_KO_overlay
    parent H3K27ac_overlay
    type bigWig
    shortLabel KO
    bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_KO.bw
    color 178,0,0
```

**Aggregate modes:**
- `transparentOverlay` -- Overlays with transparency (most common, recommended)
- `stacked` -- Stacks signals on top of each other
- `solidOverlay` -- Overlays without transparency

### SuperTracks

SuperTracks are top-level organizational folders that group multiple tracks or composites. They appear as collapsible sections in the browser.

```
track chipseqSuper
superTrack on show
shortLabel ChIP-seq Data
longLabel All ChIP-seq experiments

    track H3K27ac_composite
    parent chipseqSuper
    compositeTrack on
    shortLabel H3K27ac
    longLabel H3K27ac ChIP-seq
    type bigWig
    visibility full

        track H3K27ac_WT
        parent H3K27ac_composite on
        type bigWig
        shortLabel H3K27ac WT
        bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_WT.bw
        color 0,0,178

        track H3K27ac_KO
        parent H3K27ac_composite on
        type bigWig
        shortLabel H3K27ac KO
        bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/H3K27ac_KO.bw
        color 178,0,0

    track atacseq_peaks
    parent chipseqSuper
    type bigBed
    shortLabel ATAC peaks
    longLabel ATAC-seq peak calls
    bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/atac_peaks.bb
    color 50,150,50
    visibility pack
```

### Color and Display Settings

**Common colors (RGB):**

| Color | RGB | Use case |
|-------|-----|----------|
| Dark blue | `0,0,178` | Wild type / control signal |
| Red | `178,0,0` | Knockout / treatment signal |
| Dark green | `0,128,0` | Input / additional condition |
| Orange | `255,128,0` | Highlight / third condition |
| Black | `0,0,0` | Generic tracks |
| Grey | `128,128,128` | Input / background |

**Visibility modes:**
- `hide` -- Track not shown
- `dense` -- Collapsed to single line
- `squish` -- Compressed item display (bigBed)
- `pack` -- Full item display with labels (bigBed)
- `full` -- Full signal display (bigWig), all items with labels (bigBed)

**Signal display settings (bigWig):**
```
viewLimits 0:20           # Fixed Y-axis range from 0 to 20
autoScale off             # Disable auto-scaling (use with viewLimits)
autoScale on              # Auto-scale Y-axis to visible data range
autoScale group           # Scale all subtracks in composite to same range
maxHeightPixels 100:50:10 # Track height: max:default:min in pixels
windowingFunction mean    # How to summarize signal in bins: mean, maximum, minimum
smoothingWindow 4         # Smooth signal over N pixels
negateValues on           # Flip signal to show on negative axis (e.g., minus strand RNA-seq)
graphTypeDefault bar      # bar (filled) or points
yLineMark 0               # Draw horizontal line at Y=0
yLineOnOff on             # Enable the Y line mark
transformFunc LOG          # Apply log transform to signal
```

**Useful display pattern -- RNA-seq plus/minus strand:**
```
track rnaseq_plus
type bigWig
shortLabel RNA+ WT
bigDataUrl https://server/path/rnaseq_WT_plus.bw
color 0,0,178
visibility full
viewLimits 0:50
autoScale off
maxHeightPixels 50:30:10

track rnaseq_minus
type bigWig
shortLabel RNA- WT
bigDataUrl https://server/path/rnaseq_WT_minus.bw
color 0,0,178
visibility full
viewLimits -50:0
negateValues on
autoScale off
maxHeightPixels 50:30:10
```

### Converting Formats

All UCSC binary indexed formats require the corresponding chromosome sizes file (chrom.sizes).

**bedGraph to bigWig:**
```bash
# bedGraph MUST be sorted by chrom then start position
sort -k1,1 -k2,2n signal.bedGraph > signal.sorted.bedGraph
bedGraphToBigWig signal.sorted.bedGraph chrom.sizes signal.bw
```

**BED to bigBed:**
```bash
# BED must be sorted by chrom then start
sort -k1,1 -k2,2n peaks.bed > peaks.sorted.bed

# Standard BED (3-12 columns)
bedToBigBed peaks.sorted.bed chrom.sizes peaks.bb

# Specify BED type explicitly (e.g., narrowPeak is BED6+4)
bedToBigBed -type=bed6+4 -as=narrowPeak.as peaks.sorted.bed chrom.sizes peaks.bb
```

For MACS2 narrowPeak files, the autoSql (.as) definition file is needed:
```bash
# Download the narrowPeak autoSql definition
wget https://raw.githubusercontent.com/ucsc-oe/kent/master/src/hg/lib/encode/narrowPeak.as

# Convert narrowPeak to bigBed
sort -k1,1 -k2,2n peaks.narrowPeak > peaks.sorted.narrowPeak
bedToBigBed -type=bed6+4 -as=narrowPeak.as peaks.sorted.narrowPeak chrom.sizes peaks.bb
```

**Wiggle to bigWig:**
```bash
wigToBigWig signal.wig chrom.sizes signal.bw
```

**UCSC tools installation:**

The conversion tools (bedGraphToBigWig, bedToBigBed, wigToBigWig) are standalone binaries available from UCSC:
```bash
# Download Linux x86_64 binaries
rsync -aP rsync://hgdownload.soe.ucsc.edu/genome/admin/exe/linux.x86_64/ ./ucsc_tools/

# Or download individual tools
wget https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/bedGraphToBigWig
wget https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/bedToBigBed
wget https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/wigToBigWig
wget https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/fetchChromSizes
chmod +x bedGraphToBigWig bedToBigBed wigToBigWig fetchChromSizes
```

### Generating chrom.sizes

The chrom.sizes file is a two-column tab-separated file: chromosome name and length. It must match the assembly used for your data.

**Using fetchChromSizes (UCSC utility):**
```bash
fetchChromSizes hg38 > hg38.chrom.sizes
fetchChromSizes mm10 > mm10.chrom.sizes
fetchChromSizes dm6 > dm6.chrom.sizes
```

**From a FASTA index (samtools):**
```bash
# If you have the reference genome FASTA
samtools faidx genome.fa
cut -f1,2 genome.fa.fai > chrom.sizes
```

**From an existing BAM file header:**
```bash
samtools view -H input.bam | grep @SQ | awk '{print $2"\t"$3}' | sed 's/SN://;s/LN://' > chrom.sizes
```

### Creating bigWig from BAM

**Method 1: deeptools bamCoverage (recommended)**
```bash
# Simple RPGC-normalized bigWig
bamCoverage -b input.bam -o output.bw \
    --normalizeUsing RPGC --effectiveGenomeSize 2913022398 \
    --binSize 10 -p 8

# CPM-normalized bigWig
bamCoverage -b input.bam -o output.bw \
    --normalizeUsing CPM --binSize 10 -p 8

# Raw coverage (no normalization)
bamCoverage -b input.bam -o output.bw --binSize 10 -p 8
```

**Method 2: genomeCoverageBed + bedGraphToBigWig**
```bash
# Generate bedGraph from BAM (requires sorted BAM)
genomeCoverageBed -ibam input.bam -bg -g chrom.sizes | \
    sort -k1,1 -k2,2n > coverage.bedGraph

# Convert to bigWig
bedGraphToBigWig coverage.bedGraph chrom.sizes coverage.bw
```

This two-step method gives more control and does not require deeptools, but produces raw (unnormalized) coverage. To normalize manually:
```bash
# Get total reads for CPM normalization
total=$(samtools view -c -F 260 input.bam)
scale=$(echo "1000000 / $total" | bc -l)

genomeCoverageBed -ibam input.bam -bg -scale $scale -g chrom.sizes | \
    sort -k1,1 -k2,2n > coverage_cpm.bedGraph

bedGraphToBigWig coverage_cpm.bedGraph chrom.sizes coverage_cpm.bw
```

### Public vs Private URLs

**Public hosting (bimsbstatic.mdc-berlin.de):**

Files hosted on the institute static web server are accessible to anyone with the URL. This is ideal for sharing with collaborators and reviewers.

```
bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/project/signal.bw
```

Typical workflow for uploading:
```bash
# Copy files to the static server directory
cp signal.bw /path/to/bimsbstatic/ohler/project/

# Verify the file is accessible
curl -sI https://bimsbstatic.mdc-berlin.de/ohler/project/signal.bw | head -5
```

**Private/restricted hosting:**

If tracks are behind authentication or on an internal network, the UCSC browser cannot access them directly. Options:
- Use a publicly accessible static server (preferred)
- Set up a reverse proxy that allows UCSC IP ranges
- Use UCSC's hgCustom with uploaded data (limited file size)
- Run a local UCSC mirror or use the Genome Browser in a Box (GBiB)

**Important:** The UCSC servers at genome.ucsc.edu must be able to fetch your data files via HTTP/HTTPS. Files on local filesystems, behind VPNs, or requiring authentication will not work with the public browser.

## Key Concepts

### Binary Indexed Formats

The UCSC browser requires binary indexed formats (bigWig, bigBed) rather than their text equivalents (bedGraph, BED, wiggle) for remote data access. These formats support:
- **Random access**: The browser fetches only the data for the currently viewed region, not the entire file
- **Compression**: Files are significantly smaller than text equivalents
- **Index**: Built-in spatial index enables fast region queries over HTTP via byte-range requests

This is why the conversion step (e.g., bedGraphToBigWig) is required -- it builds the spatial index and compresses the data.

### Remote Hosting Requirements

For the UCSC browser to display your tracks:
1. Files must be served over HTTP or HTTPS
2. The web server must support byte-range requests (most static servers do, including Apache and nginx)
3. Files must be accessible without authentication from UCSC servers
4. For BAM files, the .bam.bai index must be at the same URL path
5. For VCF files, the .vcf.gz.tbi index must be at the same URL path

### Assembly Matching

Track data must match the genome assembly specified in the browser session or genomes.txt:
- A bigWig built against hg38 chromosome sizes will not display correctly on hg19
- Chromosome names must match exactly (see Common Pitfalls below)
- The chrom.sizes file used for conversion must correspond to the target assembly

## Common Pitfalls

### Unsorted bedGraph

`bedGraphToBigWig` requires the input bedGraph to be sorted by chromosome and then by start position. An unsorted file will produce an error like:

```
bedGraph input is not sorted
```

**Fix:**
```bash
sort -k1,1 -k2,2n input.bedGraph > input.sorted.bedGraph
bedGraphToBigWig input.sorted.bedGraph chrom.sizes output.bw
```

The same applies to `bedToBigBed` -- input BED files must be sorted.

### Chromosome Name Mismatches (chr1 vs 1)

This is one of the most frequent issues. UCSC assemblies use `chr`-prefixed names (chr1, chr2, chrX) while Ensembl and some other sources use bare numbers (1, 2, X). If your data uses bare chromosome names but you are viewing on a UCSC assembly (or vice versa), tracks will appear empty.

**Diagnosis:**
```bash
# Check chromosome names in your bigWig
bigWigInfo signal.bw | head -20

# Check chromosome names in your BAM
samtools view -H input.bam | grep @SQ | head -5

# Check your chrom.sizes
head -5 chrom.sizes
```

**Fix -- add chr prefix to bedGraph before conversion:**
```bash
awk '{print "chr"$0}' signal.bedGraph > signal.chr.bedGraph
```

**Fix -- add chr prefix to BAM (requires reheadering):**
```bash
samtools view -H input.bam | \
    sed 's/SN:\([0-9XY]\)/SN:chr\1/;s/SN:MT/SN:chrM/' > new_header.sam
samtools reheader new_header.sam input.bam > input.chr.bam
samtools index input.chr.bam
```

### CORS and Access Issues

If you get errors loading tracks and the files exist at the URL, check:

1. **Byte-range support**: The web server must support HTTP Range requests. Test with:
   ```bash
   curl -sI -H "Range: bytes=0-100" https://server/path/file.bw
   ```
   The response should include `Accept-Ranges: bytes` and a `206 Partial Content` status.

2. **CORS headers**: Some browser features require CORS headers. If using a custom server, ensure it sends:
   ```
   Access-Control-Allow-Origin: *
   ```

3. **HTTPS certificate**: The UCSC browser will reject self-signed certificates. Use a valid certificate or fall back to HTTP if the server supports it.

4. **File permissions**: Ensure the files are world-readable on the web server.

### Overlapping Intervals in bedGraph

`bedGraphToBigWig` does not allow overlapping intervals. If your bedGraph has overlapping regions:

```
chr1    100    200    5.0
chr1    150    250    3.0    # overlaps with previous interval
```

This will fail. Merge or resolve overlaps before conversion:
```bash
bedtools merge -i input.sorted.bedGraph -c 4 -o mean > input.merged.bedGraph
```

### Track Hub Validator

Before sharing a track hub, validate it with the UCSC hub checker:

```
https://genome.ucsc.edu/cgi-bin/hgHubConnect#unlistedHubs
```

Paste your hub.txt URL and check for errors. Common issues include:
- Missing required fields in hub.txt (hub, shortLabel, longLabel, genomesFile, email)
- Mismatched track names between parent and subtrack declarations
- Inaccessible bigDataUrl paths
- Stanza formatting errors (extra blank lines, missing blank lines between track blocks)

### Track Name Restrictions

Track names (the identifier after `track`) must:
- Contain only alphanumeric characters and underscores
- Not contain spaces, dashes, or special characters
- Be unique within a trackDb.txt file

**Wrong:**
```
track H3K27ac-WT rep1     # spaces and dashes not allowed
```

**Correct:**
```
track H3K27ac_WT_rep1
shortLabel H3K27ac WT rep1   # spaces are fine in labels
```

## Complete Track Hub Example

Here is a full working example for a project with ChIP-seq and ATAC-seq data across two conditions, hosted on bimsbstatic:

**Directory structure:**
```
myProject_hub/
  hub.txt
  genomes.txt
  hg38/
    trackDb.txt
```

**hub.txt:**
```
hub myProjectHub
shortLabel My Project
longLabel ChIP-seq and ATAC-seq from My Project 2024
genomesFile genomes.txt
email user@mdc-berlin.de
```

**genomes.txt:**
```
genome hg38
trackDb hg38/trackDb.txt
```

**hg38/trackDb.txt:**
```
track epigenomicsSuper
superTrack on show
shortLabel Epigenomics
longLabel ChIP-seq and ATAC-seq epigenomics data

    track H3K27ac_overlay
    parent epigenomicsSuper
    container multiWig
    shortLabel H3K27ac
    longLabel H3K27ac ChIP-seq WT vs KO overlay
    type bigWig
    visibility full
    maxHeightPixels 100:50:10
    viewLimits 0:25
    autoScale off
    aggregate transparentOverlay
    showSubtrackColorOnUi on

        track H3K27ac_WT
        parent H3K27ac_overlay
        type bigWig
        shortLabel H3K27ac WT
        longLabel H3K27ac ChIP-seq wild type merged
        bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/myProject/H3K27ac_WT.bw
        color 0,0,178

        track H3K27ac_KO
        parent H3K27ac_overlay
        type bigWig
        shortLabel H3K27ac KO
        longLabel H3K27ac ChIP-seq knockout merged
        bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/myProject/H3K27ac_KO.bw
        color 178,0,0

    track atacseq_composite
    parent epigenomicsSuper
    compositeTrack on
    shortLabel ATAC-seq
    longLabel ATAC-seq signal and peaks
    type bigWig
    visibility full

        track ATAC_WT
        parent atacseq_composite on
        type bigWig
        shortLabel ATAC WT
        longLabel ATAC-seq wild type
        bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/myProject/ATAC_WT.bw
        color 0,128,0
        maxHeightPixels 80:40:10
        viewLimits 0:30
        autoScale off

        track ATAC_KO
        parent atacseq_composite on
        type bigWig
        shortLabel ATAC KO
        longLabel ATAC-seq knockout
        bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/myProject/ATAC_KO.bw
        color 255,128,0
        maxHeightPixels 80:40:10
        viewLimits 0:30
        autoScale off

        track ATAC_peaks_WT
        parent atacseq_composite on
        type bigBed
        shortLabel Peaks WT
        longLabel ATAC-seq peaks wild type
        bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/myProject/ATAC_peaks_WT.bb
        color 0,128,0
        visibility dense

        track ATAC_peaks_KO
        parent atacseq_composite on
        type bigBed
        shortLabel Peaks KO
        longLabel ATAC-seq peaks knockout
        bigDataUrl https://bimsbstatic.mdc-berlin.de/ohler/myProject/ATAC_peaks_KO.bb
        color 255,128,0
        visibility dense
```

**Browser link to share:**
```
https://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38&hubUrl=https://bimsbstatic.mdc-berlin.de/ohler/myProject/hub.txt
```

## Shell Script: Create Track Hub Scaffold

```bash
#!/bin/bash
# Usage: create_hub.sh <hub_dir> <hub_name> <email> <assembly>
# Example: create_hub.sh myHub "My Project" user@mdc-berlin.de hg38

hub_dir="$1"
hub_name="$2"
email="$3"
assembly="${4:-hg38}"

mkdir -p "${hub_dir}/${assembly}"

cat > "${hub_dir}/hub.txt" << EOF
hub $(echo "${hub_name}" | tr ' ' '_')
shortLabel ${hub_name}
longLabel ${hub_name}
genomesFile genomes.txt
email ${email}
EOF

cat > "${hub_dir}/genomes.txt" << EOF
genome ${assembly}
trackDb ${assembly}/trackDb.txt
EOF

cat > "${hub_dir}/${assembly}/trackDb.txt" << EOF
# Add track stanzas below
# Example:
# track myTrack
# type bigWig
# shortLabel My Track
# longLabel My Track description
# bigDataUrl https://bimsbstatic.mdc-berlin.de/path/to/file.bw
# color 0,0,178
# visibility full
EOF

echo "Track hub scaffold created in ${hub_dir}/"
echo "Edit ${hub_dir}/${assembly}/trackDb.txt to add your tracks"
```
