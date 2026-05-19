---
name: guix
description: GNU Guix package manager. Create reproducible environments with profiles and manifests, manage packages declaratively, build isolated development shells, and ensure bitwise-reproducible scientific computing setups.
license: MIT license
metadata:
    skill-author: VFranke
---

# GNU Guix: Reproducible Package Management for Scientific Computing

## Overview

GNU Guix is a functional package manager and system distribution built on top of GNU Guile Scheme. It provides transactional upgrades and rollbacks, unprivileged package management, per-user profiles, declarative environment configuration through manifest files, and bit-for-bit reproducible builds. Every package is stored as an immutable artifact in `/gnu/store`, identified by a hash of all its inputs, making environments fully reproducible across machines and over time.

For bioinformaticians working on shared Linux systems, Guix solves the persistent problem of dependency conflicts, version pinning, and environment reproducibility without requiring root access or containers. You can maintain completely separate tool stacks for different projects, share exact environment specifications with collaborators, and reproduce any past environment by referencing a specific Guix commit.

## When to Use This Skill

Use this skill when:

- Installing bioinformatics tools (samtools, bedtools, STAR, hisat2, salmon, etc.) without root access
- Creating reproducible, project-specific environments with exact package versions
- Managing multiple R/Bioconductor or Python environments side by side
- Setting up ephemeral shells for one-off tasks or testing different tool versions
- Pinning an entire software stack to a specific point in time for publication reproducibility
- Building packages from source with custom patches or configurations
- Isolating environments using lightweight containers without Docker
- Sharing environment definitions with collaborators via manifest files
- Rolling back after a broken upgrade

## Quick Start

### Install a single package into your default profile

```bash
guix install samtools
```

### Search for available packages

```bash
guix search bioinformatics
guix search "samtools"
```

### Start an ephemeral shell with specific tools

```bash
guix shell samtools bedtools htslib -- samtools --version
```

### Create a profile from a manifest file

```bash
guix package -m manifest.scm -p ~/my-project-profile
source ~/my-project-profile/etc/profile
```

### Check what you have installed

```bash
guix package --list-installed
```

## Core Capabilities

### 1. Package Operations

Guix provides a complete set of commands for managing packages in your profile.

**Installing packages:**

```bash
# Install one or more packages
guix install samtools bcftools htslib

# Install a specific version (if available as a separate package)
guix install python@3.10

# Install with a specific output (some packages have multiple outputs)
guix install glib:bin
```

**Removing packages:**

```bash
guix remove samtools
```

**Upgrading packages:**

```bash
# Upgrade all installed packages (after guix pull)
guix upgrade

# Upgrade specific packages
guix upgrade samtools bcftools
```

**Searching and inspecting packages:**

```bash
# Full-text search across package names and descriptions
guix search RNA-seq
guix search "multiple sequence alignment"

# Show detailed info about a specific package
guix show samtools
guix show r-deseq2

# List all installed packages
guix package --list-installed

# List available package versions
guix package --list-available=samtools
```

**Listing generations and rolling back:**

```bash
# List profile generations (snapshots of installed packages)
guix package --list-generations

# Roll back to the previous generation
guix package --roll-back

# Switch to a specific generation
guix package --switch-generation=5
```

### 2. Profiles

Profiles are Guix's mechanism for maintaining separate sets of installed packages. Each profile is a directory containing `bin/`, `lib/`, `etc/profile`, and other standard directories, all composed from the packages installed into that profile.

**Default profile:**

Your default profile is `~/.guix-profile`. When you run `guix install`, packages go here.

**Named profiles for project isolation:**

```bash
# Create or update a profile for a specific project
guix package -p ~/.guix-extra-profiles/rnaseq -i samtools star htseq r-deseq2

# Activate the profile in your current shell
source ~/.guix-extra-profiles/rnaseq/etc/profile

# Each profile has independent generations
guix package -p ~/.guix-extra-profiles/rnaseq --list-generations
guix package -p ~/.guix-extra-profiles/rnaseq --roll-back
```

**Listing installed packages in a specific profile:**

```bash
guix package -p ~/.guix-extra-profiles/rnaseq --list-installed
```

**Removing a profile entirely:**

Simply delete the profile symlink and run garbage collection:

```bash
rm ~/.guix-extra-profiles/old-project
guix gc
```

### 3. Manifests

Manifests are Guile Scheme files that declaratively specify a set of packages. They are the recommended way to define reproducible environments.

**Basic manifest (manifest.scm):**

```scheme
(specifications->manifest
 '("samtools"
   "bcftools"
   "htslib"
   "bedtools"
   "r-minimal"
   "r-deseq2"
   "r-ggplot2"
   "python"
   "python-numpy"
   "python-pandas"))
```

**Installing a manifest into a profile:**

```bash
guix package -m manifest.scm -p ~/.guix-extra-profiles/rnaseq
source ~/.guix-extra-profiles/rnaseq/etc/profile
```

**Manifest with version constraints:**

```scheme
(specifications->manifest
 '("samtools@1.17"
   "python@3.10"
   "r-minimal@4.3"))
```

**Manifest with package transformations:**

```scheme
(use-modules (guix transformations))

(define transform
  (options->transformation
   '((with-latest . "samtools"))))

(packages->manifest
 (map transform
      (specifications->packages
       '("samtools" "bcftools"))))
```

**Combining multiple manifests:**

```scheme
(concatenate-manifests
 (list
  (specifications->manifest
   '("samtools" "bcftools" "bedtools"))
  (specifications->manifest
   '("r-minimal" "r-deseq2" "r-ggplot2"))))
```

### 4. Ephemeral Shells

`guix shell` creates temporary environments that disappear when the shell exits. This is ideal for one-off tasks, testing, and running tools you do not want to install permanently.

**Basic usage:**

```bash
# Enter a shell with specific packages
guix shell samtools bcftools

# Run a single command in the environment
guix shell samtools -- samtools view -h input.bam | head

# Use a manifest file
guix shell -m manifest.scm
```

**Pure shells (clean environment):**

```bash
# --pure removes most environment variables, giving a clean slate
guix shell --pure samtools bcftools -- samtools --version

# Preserve specific variables in a pure shell
guix shell --pure -E DISPLAY -E HOME samtools -- samtools
```

**Development shells:**

```bash
# -D brings in the build dependencies of a package (useful for developing that package)
guix shell -D samtools
# You now have gcc, htslib headers, autoconf, etc. -- everything needed to build samtools
```

**Shell with a manifest:**

```bash
guix shell -m manifest.scm
```

**Automatic shell activation:**

Place a `manifest.scm` in your project directory. When you run `guix shell` with no arguments from that directory, Guix will use the manifest automatically (after confirmation).

### 5. Channels

Channels are Git repositories containing package definitions. The default channel is the official GNU Guix repository, but you can add custom channels for additional packages.

**Listing current channels:**

```bash
guix describe
```

**Custom channels file (channels.scm):**

```scheme
(list
 (channel
  (name 'guix)
  (url "https://git.savannah.gnu.org/git/guix.git")
  ;; Pin to a specific commit for reproducibility
  (commit "a]1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"))
 (channel
  (name 'guix-bioinformatics)
  (url "https://github.com/UMCUGenetics/guix-genomics.git")))
```

**Pulling from specific channels:**

```bash
guix pull --channels=channels.scm
```

**After pulling, new packages and updates are available:**

```bash
guix pull
# Now 'guix' commands use the newly fetched package definitions
guix upgrade
```

### 6. Environment Reproducibility

Guix provides multiple mechanisms to ensure exact reproducibility of software environments.

**Describe the current Guix state:**

```bash
# Show the exact channel commits in use
guix describe

# Output in a format suitable for sharing
guix describe -f channels
```

**Save your channel state for reproducibility:**

```bash
guix describe -f channels > channels.scm
```

A collaborator can then reproduce your exact environment:

```bash
guix pull -C channels.scm
guix package -m manifest.scm -p ./profile
```

**Time machine (use a specific historical Guix version):**

```bash
# Run a command using Guix as it was at a specific commit
guix time-machine --channels=channels.scm -- shell -m manifest.scm

# Install into a profile using a pinned Guix
guix time-machine --channels=channels.scm -- package -m manifest.scm -p ./profile
```

**Full reproducibility recipe for a project:**

Keep these two files in version control:

1. `channels.scm` -- the exact Guix channel commits
2. `manifest.scm` -- the list of packages

Any collaborator can reproduce the environment:

```bash
guix time-machine -C channels.scm -- shell -m manifest.scm
```

### 7. Building from Source

Guix can build any package from source, and provides transformation options to modify builds.

**Build a package:**

```bash
# Build and print the store path
guix build samtools

# Build with source substitution (use your own tarball)
guix build samtools --with-source=samtools=./samtools-1.18.tar.bz2

# Build with a patch applied
guix build samtools --with-patch=samtools=./my-fix.patch
```

**Check build reproducibility:**

```bash
guix build samtools --check
```

**View the build log:**

```bash
guix build --log-file samtools
```

### 8. Containers

`guix shell --container` provides lightweight isolation using Linux namespaces, without needing Docker or root access.

**Basic container:**

```bash
# Run a shell in an isolated container
guix shell --container samtools bcftools

# The container has only the specified packages -- no host programs leak in
```

**Exposing directories:**

```bash
# Share a host directory read-only
guix shell --container --share=/data/references samtools -- \
  samtools view /data/references/sample.bam | head

# Share read-write
guix shell --container --share=/scratch/output=/output samtools
```

**Container with network access:**

```bash
guix shell --container --network samtools curl
```

**Combining container with manifest:**

```bash
guix shell --container -m manifest.scm --share=/data
```

### 9. Garbage Collection

Guix stores all packages in `/gnu/store`. Over time, old generations and unused packages accumulate. Garbage collection reclaims this space.

**Basic garbage collection:**

```bash
# Remove store items not reachable from any profile generation
guix gc
```

**Delete old profile generations first (frees more space):**

```bash
# Delete all generations older than 30 days from default profile
guix package --delete-generations=30d

# Delete old generations from a specific profile
guix package -p ~/.guix-extra-profiles/rnaseq --delete-generations=60d

# Then collect garbage
guix gc
```

**Check store size:**

```bash
guix gc --list-dead | wc -l   # count unreachable store items
guix gc --list-live | wc -l   # count reachable store items
du -sh /gnu/store              # total store size (requires read access)
```

**Free a specific amount of space:**

```bash
guix gc -F 10G   # free at least 10 GB
```

## Patterns for Scientific Computing

### Per-Project Profiles in ~/.guix-extra-profiles/

A common pattern for bioinformaticians is to maintain separate profiles for each project or analysis type under `~/.guix-extra-profiles/`:

```
~/.guix-extra-profiles/
  rnaseq/           # RNA-seq analysis tools
  chipseq/          # ChIP-seq analysis tools
  scrnaseq/         # Single-cell RNA-seq tools
  variant-calling/  # Variant calling pipeline
```

Each has its own manifest:

```bash
guix package -m ~/projects/rnaseq/manifest.scm -p ~/.guix-extra-profiles/rnaseq
guix package -m ~/projects/chipseq/manifest.scm -p ~/.guix-extra-profiles/chipseq
```

### Activation Functions in .bashrc

Define shell functions to quickly activate project environments:

```bash
# In ~/.bashrc

# Generic profile activation function
activate_profile() {
    local profile="$HOME/.guix-extra-profiles/$1"
    if [ -d "$profile" ]; then
        export GUIX_PROFILE="$profile"
        source "$profile/etc/profile"
        echo "Activated Guix profile: $1"
    else
        echo "Profile not found: $profile"
        return 1
    fi
}

# Convenience aliases
alias rnaseq='activate_profile rnaseq'
alias chipseq='activate_profile chipseq'
alias scrnaseq='activate_profile scrnaseq'
```

Usage:

```bash
rnaseq          # activates the RNA-seq profile
which samtools  # points to /gnu/store/...-samtools-.../bin/samtools
```

### R + Bioconductor Packages via Guix

Guix packages many R and Bioconductor packages. They are prefixed with `r-` in Guix.

```bash
# Search for R packages
guix search r-deseq2
guix search r-bioconductor

# Common R/Bioconductor manifest for RNA-seq
```

**manifest.scm for an R-based RNA-seq analysis:**

```scheme
(specifications->manifest
 '(;; R base
   "r-minimal"

   ;; Bioconductor - differential expression
   "r-deseq2"
   "r-edger"
   "r-limma"

   ;; Bioconductor - genomic ranges
   "r-genomicranges"
   "r-genomicfeatures"
   "r-genomicalignments"
   "r-rtracklayer"
   "r-biostrings"

   ;; Bioconductor - annotation
   "r-org-hs-eg-db"
   "r-annotationdbi"

   ;; Visualization
   "r-ggplot2"
   "r-pheatmap"
   "r-complexheatmap"
   "r-enhancedvolcano"

   ;; Data manipulation
   "r-dplyr"
   "r-tidyr"
   "r-data-table"
   "r-readr"))
```

Install and activate:

```bash
guix package -m manifest.scm -p ~/.guix-extra-profiles/r-rnaseq
source ~/.guix-extra-profiles/r-rnaseq/etc/profile
R  # launches R with all the above packages available
```

### Python Packages via Guix

Python packages in Guix are prefixed with `python-`.

**manifest.scm for a Python data science environment:**

```scheme
(specifications->manifest
 '("python"
   "python-numpy"
   "python-scipy"
   "python-pandas"
   "python-matplotlib"
   "python-seaborn"
   "python-scikit-learn"
   "python-scanpy"
   "python-anndata"
   "python-loompy"
   "python-pysam"
   "python-htseq"
   "python-jupyter"
   "python-ipython"))
```

**Note on PYTHONPATH:** When you activate a Guix profile, `PYTHONPATH` is set to include the Guix-provided Python packages. Avoid mixing `pip install` into the same environment, as this can cause conflicts. If you need packages not in Guix, consider using a separate virtual environment layered on top:

```bash
source ~/.guix-extra-profiles/python-bio/etc/profile
python -m venv --system-site-packages ./venv
source ./venv/bin/activate
pip install some-package-not-in-guix
```

### Mixing Guix with Conda When Needed

Sometimes a specific tool is only available through conda (or bioconda) and not yet packaged in Guix. In these cases, you can use both, but must be careful about environment interactions.

**Strategy: keep them separate and explicit.**

```bash
# Activate your Guix profile first for the core tools
source ~/.guix-extra-profiles/rnaseq/etc/profile

# Then activate a minimal conda environment for the one tool you need
conda activate my-special-tool

# Be aware that conda may override PATH entries from Guix.
# Check which binary is being used:
which samtools   # should confirm it comes from the expected manager
```

**Best practices for mixing:**

- Use Guix as the primary package manager for all tools that are available in Guix.
- Only use conda for tools not packaged in Guix.
- Keep conda environments minimal (one or two tools per environment).
- Always verify `which <tool>` after activating both to confirm PATH ordering.
- Document which tools come from which manager in your project README.
- Consider packaging the missing tool for Guix to eliminate the conda dependency long-term.

## Key Concepts

### The Store (/gnu/store)

All packages built or downloaded by Guix live in `/gnu/store`. Each item is stored under a path like:

```
/gnu/store/abc123...-samtools-1.17/
```

The hash (`abc123...`) is derived from all inputs to the build: source code, dependencies, compiler flags, and build scripts. This means:

- Two builds with identical inputs always produce identical store paths.
- Different versions or configurations always produce different store paths.
- Multiple versions can coexist without conflict.
- Store items are immutable -- once built, they are never modified.

### Generations

Every time you install, remove, or upgrade packages in a profile, Guix creates a new generation. Generations are numbered snapshots that you can switch between:

```bash
guix package --list-generations
# Generation 1   Jan 15 2025 10:00:00
#   samtools 1.17  out  /gnu/store/...-samtools-1.17
# Generation 2   Jan 20 2025 14:30:00
#   samtools 1.17  out  /gnu/store/...-samtools-1.17
#   bcftools 1.17  out  /gnu/store/...-bcftools-1.17
```

This provides an undo mechanism: if an upgrade breaks something, roll back instantly.

### Profiles

A profile is a union of packages, represented as a directory of symlinks into `/gnu/store`. Activating a profile (`source profile/etc/profile`) sets `PATH`, `PYTHONPATH`, `R_LIBS_SITE`, `PKG_CONFIG_PATH`, and other environment variables to point to the packages in that profile.

### Functional Package Management

Guix treats package management like a pure function: given the same inputs (source, dependencies, build recipe), you always get the same output. There are no hidden global states, no mutation of installed packages, and no dependency on system-wide libraries (other than the kernel). This is what makes Guix environments truly reproducible.

### Guile Scheme

Guix uses GNU Guile (a Scheme dialect) as its configuration and extension language. Manifests, channel specifications, package definitions, and system configurations are all written in Guile. You do not need to be a Scheme expert to use manifests -- the `specifications->manifest` pattern covers most use cases -- but knowing basic Scheme syntax helps when you need advanced transformations.

Basic Scheme syntax for Guix users:

```scheme
;; This is a comment
;; A list of strings
'("samtools" "bcftools" "bedtools")

;; Function call
(specifications->manifest '("samtools"))

;; Importing modules
(use-modules (guix transformations))

;; Defining a variable
(define my-packages '("samtools" "bcftools"))
```

## Common Pitfalls

### SSL/TLS Certificate Issues

On non-Guix systems (where Guix is installed as a standalone package manager), Guix-installed programs may not find SSL certificates. Fix this by exporting the certificate bundle path:

```bash
# Add to your .bashrc
export SSL_CERT_DIR="$HOME/.guix-profile/etc/ssl/certs"
export SSL_CERT_FILE="$HOME/.guix-profile/etc/ssl/certs/ca-certificates.crt"
export GIT_SSL_CAINFO="$SSL_CERT_FILE"

# Make sure nss-certs is installed
guix install nss-certs
```

### Locale Issues

Guix-installed programs may complain about missing locales (`locale: Cannot set LC_ALL`). Install the locale data:

```bash
guix install glibc-locales

# Add to your .bashrc
export GUIX_LOCPATH="$HOME/.guix-profile/lib/locale"
```

### PATH Ordering with Other Package Managers

When mixing Guix with system packages, conda, or other managers, PATH ordering determines which binary runs. Common issues:

```bash
# Check which binary is actually being used
which python
type -a python   # shows ALL python binaries in PATH

# Guix profile activation prepends to PATH, so it takes priority
# If you activate conda after Guix, conda may override Guix binaries
```

**Recommendation:** Activate Guix profiles first, then other environments. Use `which` to verify.

### Shared Systems: Guix Daemon and Substitutes

On shared systems, the Guix daemon runs as root and manages `/gnu/store`. If substitutes (pre-built binaries) are not configured, builds can be very slow because everything compiles from source. Check with your system administrator that the substitute servers are authorized:

```bash
# Check substitute server configuration
guix describe
# Look for "substitute URLs" in the output
```

If builds are unexpectedly slow, substitutes may be unavailable for your requested packages. You can check:

```bash
guix weather samtools   # check substitute availability
```

### Profile Conflicts

Installing two packages that provide the same file into one profile will cause a conflict. Guix will report the conflict and refuse the operation. Solutions:

- Use separate profiles for conflicting tools.
- Use `guix shell` for ephemeral access to one of the conflicting tools.
- Use the `--allow-collisions` flag as a last resort (not recommended).

### Forgetting to Source Profile

A common mistake is installing packages into a profile but forgetting to source it:

```bash
guix package -m manifest.scm -p ~/.guix-extra-profiles/myproject
# Tools are NOT yet on your PATH
source ~/.guix-extra-profiles/myproject/etc/profile
# Now they are
```

### Large Store Size

Guix stores all versions of all packages. The store can grow very large. Regularly clean up:

```bash
# Delete generations older than 60 days across all your profiles
guix package --delete-generations=60d
guix package -p ~/.guix-extra-profiles/rnaseq --delete-generations=60d
# ... repeat for other profiles

# Then collect garbage
guix gc
```
