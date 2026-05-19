---
name: tmux-sessions
description: Tmux session management for bioinformatics. Organize project sessions with named windows, split panes for monitoring jobs, manage persistent long-running analyses, and script reproducible tmux layouts.
license: MIT license
metadata:
    skill-author: VFranke
---

# Tmux Session Management for Bioinformatics

## Overview

Tmux (terminal multiplexer) is an essential tool for bioinformatics work on remote servers. It allows you to maintain persistent terminal sessions that survive SSH disconnections, organize work across multiple projects, and monitor long-running analyses. This skill covers session, window, and pane management with a focus on patterns that arise in computational biology workflows -- managing many concurrent projects, keeping interactive R and Python sessions alive, monitoring cluster jobs, and scripting reproducible workspace layouts.

## When to Use

- You need to run analyses that take hours or days and must survive SSH disconnects.
- You are working on multiple projects simultaneously (urine, apom, ang, nb, cdep, cache, kim, land, etc.) and need to keep each project's context organized and quickly accessible.
- You want to monitor long-running jobs in a split pane while continuing to work.
- You need to script a reproducible tmux layout so you can recreate your working environment after a server reboot.
- You want to keep an interactive R or Python session alive across work sessions.
- You need to send commands to a running session from a script or cron job.

## Quick Start

```bash
# Start a new named session for a project
tmux new -s urine

# Detach from the session (inside tmux)
# Ctrl-b d

# List all running sessions
tmux ls

# Reattach to a session by name
tmux a -t urine

# Using the "tt" alias (equivalent to tmux a -t)
tt urine

# Kill a session you no longer need
tmux kill-session -t old_project
```

## Key Concepts: Session, Window, and Pane Hierarchy

Tmux organizes terminals in a three-level hierarchy:

```
tmux server
  |
  +-- session: urine
  |     +-- window 0: analysis    [pane 0] [pane 1]
  |     +-- window 1: plots       [pane 0]
  |     +-- window 2: monitoring  [pane 0] [pane 1] [pane 2]
  |
  +-- session: apom
  |     +-- window 0: preprocessing [pane 0]
  |     +-- window 1: results       [pane 0]
  |
  +-- session: ang
        +-- window 0: main        [pane 0]
```

- **Session**: A named collection of windows. Use one session per project. Sessions persist on the server even when you disconnect.
- **Window**: A full-screen tab within a session. Use windows to separate different tasks within a project (e.g., analysis, plotting, monitoring).
- **Pane**: A subdivision of a window. Use panes to see multiple terminals side by side (e.g., editor on the left, running process on the right).

The tmux server runs in the background and keeps all sessions alive. When you detach (Ctrl-b d) or lose your SSH connection, everything continues running. You simply reattach later.

## Core Capabilities

### Session Management

```bash
# Create a new named session
tmux new -s kim

# Create a new session in detached mode (useful for scripting)
tmux new -s kim -d

# List all sessions
tmux ls

# Attach to a session by name
tmux a -t kim
# Or using the alias:
tt kim

# Detach from current session
# Ctrl-b d

# Rename the current session
# Ctrl-b $
# Or from the command line:
tmux rename-session -t old_name new_name

# Kill a specific session
tmux kill-session -t kim

# Kill all sessions except the current one
tmux kill-session -a

# Switch between sessions (inside tmux)
# Ctrl-b s    -- interactive session chooser
# Ctrl-b (    -- previous session
# Ctrl-b )    -- next session
```

### Window Management

```bash
# Create a new window with a name
tmux new-window -n analysis

# Or inside tmux:
# Ctrl-b c         -- create new window
# Ctrl-b ,         -- rename current window

# Navigate between windows
# Ctrl-b n         -- next window
# Ctrl-b p         -- previous window
# Ctrl-b 0-9       -- jump to window by number
# Ctrl-b w         -- interactive window chooser

# Select a window by name or index from the command line
tmux select-window -t analysis
tmux select-window -t 2

# List windows in a session
tmux list-windows -t urine

# Move or swap windows
tmux swap-window -s 2 -t 0

# Kill the current window
# Ctrl-b &
```

### Pane Management

```bash
# Split the current pane horizontally (top/bottom)
# Ctrl-b "
tmux split-window -v

# Split the current pane vertically (left/right)
# Ctrl-b %
tmux split-window -h

# Navigate between panes
# Ctrl-b <arrow key>    -- move to pane in that direction
# Ctrl-b o              -- cycle through panes
# Ctrl-b q              -- show pane numbers, then press number to jump

# Resize panes
# Ctrl-b Ctrl-<arrow>   -- resize in that direction
# Or from the command line:
tmux resize-pane -D 10    # down 10 rows
tmux resize-pane -U 5     # up 5 rows
tmux resize-pane -L 20    # left 20 columns
tmux resize-pane -R 20    # right 20 columns

# Zoom a pane to full screen (toggle)
# Ctrl-b z

# Close current pane
# Ctrl-b x
# Or simply type exit / Ctrl-d in the pane

# Convert a pane into its own window
# Ctrl-b !
```

### Copy Mode

```bash
# Enter copy mode
# Ctrl-b [

# In copy mode (vi-style bindings):
#   /         -- search forward
#   ?         -- search backward
#   n         -- next match
#   N         -- previous match
#   Space     -- start selection
#   Enter     -- copy selection
#   q         -- exit copy mode
#   g         -- go to top
#   G         -- go to bottom
#   Ctrl-u    -- page up
#   Ctrl-d    -- page down

# Paste the copied text
# Ctrl-b ]
```

Copy mode is essential for scrolling back through long outputs, such as reviewing build logs or error messages from a pipeline that scrolled past.

### Sending Commands to Running Sessions

You can send keystrokes to any tmux pane from outside, which is powerful for automation:

```bash
# Send a command to a specific session and window
tmux send-keys -t urine:analysis "Rscript run_deseq2.R" C-m

# Send to a specific pane (session:window.pane)
tmux send-keys -t ang:0.1 "htop" C-m

# Send Ctrl-C to cancel a running process
tmux send-keys -t kim:monitoring C-c

# Send multiple commands in sequence
tmux send-keys -t cdep:0 "cd /data/projects/cdep" C-m
tmux send-keys -t cdep:0 "conda activate cdep_env" C-m
tmux send-keys -t cdep:0 "snakemake --cores 16" C-m
```

The `C-m` at the end simulates pressing Enter. This mechanism is useful for scripting session setup and for sending commands from cron jobs or wrapper scripts.

### Scripting Tmux Layouts

You can script an entire tmux workspace so it can be recreated reliably after a reboot or on a new server:

```bash
#!/bin/bash
# setup_urine.sh -- Recreate the urine project workspace

SESSION="urine"

# Kill existing session if present
tmux kill-session -t $SESSION 2>/dev/null

# Create session with first window named "analysis"
tmux new-session -d -s $SESSION -n analysis

# Set up the analysis window
tmux send-keys -t $SESSION:analysis "cd /data/projects/urine" C-m
tmux send-keys -t $SESSION:analysis "conda activate urine_env" C-m

# Split for monitoring
tmux split-window -h -t $SESSION:analysis
tmux send-keys -t $SESSION:analysis.1 "watch -n 30 squeue -u $USER" C-m

# Create a second window for R work
tmux new-window -t $SESSION -n R
tmux send-keys -t $SESSION:R "cd /data/projects/urine/scripts" C-m
tmux send-keys -t $SESSION:R "R" C-m

# Create a third window for file browsing
tmux new-window -t $SESSION -n files
tmux send-keys -t $SESSION:files "cd /data/projects/urine/results" C-m

# Go back to the first window
tmux select-window -t $SESSION:analysis

# Attach
tmux attach -t $SESSION
```

A more complex layout with multiple splits:

```bash
#!/bin/bash
# setup_pipeline.sh -- Layout for monitoring a pipeline run

SESSION="pipeline"
tmux kill-session -t $SESSION 2>/dev/null

tmux new-session -d -s $SESSION -n monitor

# Main pane: run the pipeline
tmux send-keys -t $SESSION:monitor "cd /data/projects/ang && snakemake -n" C-m

# Bottom pane: watch cluster queue
tmux split-window -v -t $SESSION:monitor -p 30
tmux send-keys -t $SESSION:monitor.1 "watch -n 10 squeue -u $USER" C-m

# Right pane on top: watch output directory
tmux select-pane -t $SESSION:monitor.0
tmux split-window -h -t $SESSION:monitor -p 40
tmux send-keys -t $SESSION:monitor.1 "watch -n 60 'ls -lhrt /data/projects/ang/results/ | tail -20'" C-m

tmux select-pane -t $SESSION:monitor.0
tmux attach -t $SESSION
```

### Configuration (~/.tmux.conf)

The tmux configuration file lets you customize key bindings, appearance, and behavior:

```bash
# ~/.tmux.conf

# ------- General -------

# Increase scrollback history
set -g history-limit 50000

# Start window and pane numbering at 1
set -g base-index 1
setw -g pane-base-index 1

# Renumber windows when one is closed
set -g renumber-windows on

# Reduce escape key delay (important for vim/neovim users)
set -sg escape-time 10

# Enable mouse mode (scroll, select pane, resize pane)
set -g mouse on

# Use 256 colors
set -g default-terminal "screen-256color"

# ------- Key bindings -------

# Reload config
bind r source-file ~/.tmux.conf \; display "Config reloaded"

# More intuitive split keys
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# New window in current path
bind c new-window -c "#{pane_current_path}"

# Vi-style pane navigation
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Pane resizing
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# Vi-style copy mode
setw -g mode-keys vi
bind -T copy-mode-vi v send -X begin-selection
bind -T copy-mode-vi y send -X copy-selection-and-cancel

# ------- Status bar -------

set -g status-position bottom
set -g status-interval 5
set -g status-left-length 40
set -g status-left "#[fg=green]#S #[fg=white]| "
set -g status-right "#[fg=cyan]%Y-%m-%d %H:%M"
```

After editing `~/.tmux.conf`, reload it inside tmux with:

```bash
tmux source-file ~/.tmux.conf
```

Or if you added the bind from the example above, press `Ctrl-b r`.

## Bioinformatics Patterns

### One Session Per Project

Maintain a named session for each active project. This keeps contexts cleanly separated and lets you jump between projects instantly:

```bash
# Your typical running sessions
tmux ls
# ang: 3 windows (created Mon Feb 16 09:12:00 2026)
# apom: 2 windows (created Mon Feb 16 09:15:00 2026)
# cache: 1 windows (created Tue Feb 17 14:30:00 2026)
# cdep: 2 windows (created Mon Feb 16 10:00:00 2026)
# kim: 1 windows (created Wed Feb 18 08:45:00 2026)
# land: 2 windows (created Mon Feb 16 11:20:00 2026)
# nb: 3 windows (created Mon Feb 16 09:30:00 2026)
# urine: 4 windows (created Mon Feb 16 08:00:00 2026)

# Quick switch
tt urine
# Ctrl-b s to browse and select
```

### Monitoring Long-Running Jobs

Split a pane to keep an eye on cluster jobs while you work:

```bash
# In your working pane, split horizontally
# Ctrl-b "

# In the new pane, run a watch command
watch -n 30 squeue -u $USER

# Or monitor a specific job's output
tail -f /data/projects/urine/logs/alignment_job_12345.log

# Toggle zoom on your working pane to get full screen back
# Ctrl-b z
```

### Session Scripts for Reproducible Environments

Create a script for each project that sets up the complete environment:

```bash
#!/bin/bash
# ~/bin/start_apom.sh

SESSION="apom"
tmux has-session -t $SESSION 2>/dev/null

if [ $? != 0 ]; then
    tmux new-session -d -s $SESSION -n main
    tmux send-keys -t $SESSION:main "cd /data/projects/apom" C-m
    tmux send-keys -t $SESSION:main "source activate apom_env" C-m

    tmux new-window -t $SESSION -n R
    tmux send-keys -t $SESSION:R "cd /data/projects/apom/analysis" C-m
    tmux send-keys -t $SESSION:R "R" C-m

    tmux select-window -t $SESSION:main
fi

tmux attach -t $SESSION
```

This pattern checks whether the session already exists before creating it, so the script is safe to run repeatedly.

### Keeping R and Python Sessions Alive Across SSH Disconnects

One of the most valuable uses of tmux in bioinformatics is preserving interactive sessions:

```bash
# Start or attach to your project session
tt nb

# Launch R -- it will persist even if your laptop goes to sleep
R

# Load your data, run analyses...
# When you need to leave, simply detach:
# Ctrl-b d

# Later, from home, SSH back in and reattach:
ssh server
tt nb
# Your R session is exactly where you left it, objects still in memory
```

This works identically for Python, IPython, Julia, or any interactive program. The tmux server keeps the process alive on the remote machine regardless of your SSH connection status.

### Sending Commands from External Scripts

Automate repetitive tasks by sending commands to existing sessions:

```bash
#!/bin/bash
# After a pipeline finishes, notify the R session to reload results

# Send to the R window in the urine session
tmux send-keys -t urine:R "message('Pipeline complete -- reloading results')" C-m
tmux send-keys -t urine:R "results <- readRDS('results/deseq2_output.rds')" C-m
```

This is useful in pipeline wrappers or as a post-processing step in cluster job scripts.

## Common Pitfalls

### Nested Tmux Sessions

If you SSH from inside tmux into another machine that also runs tmux, you can end up with tmux inside tmux. The prefix key (Ctrl-b) will be captured by the outer session.

To send the prefix to the inner session, press the prefix twice: `Ctrl-b Ctrl-b`, then your command key.

Alternatively, set a different prefix for the inner tmux in its configuration:

```bash
# On the remote machine's ~/.tmux.conf
set -g prefix C-a
unbind C-b
bind C-a send-prefix
```

### TERM Variable Issues

Programs inside tmux may misbehave if the TERM variable is not set correctly. If you see garbled colors or broken line drawing:

```bash
# In ~/.tmux.conf
set -g default-terminal "screen-256color"

# If you use true color (24-bit), also add:
set -ga terminal-overrides ",xterm-256color:Tc"
```

If a program complains about the terminal type, check:

```bash
echo $TERM
# Should show "screen-256color" or "tmux-256color" inside tmux
```

### Clipboard Integration

Copying text from tmux to your system clipboard requires extra configuration, especially over SSH:

```bash
# In ~/.tmux.conf -- for systems with xclip
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "xclip -selection clipboard"

# For macOS (if you ever work locally)
# bind -T copy-mode-vi y send -X copy-pipe-and-cancel "pbcopy"
```

Over SSH, clipboard integration typically requires X11 forwarding (`ssh -X`) or using OSC 52 escape sequences if your terminal emulator supports them.

### Session Accumulation

With many projects, sessions can accumulate. Periodically clean up sessions you no longer need:

```bash
# List sessions with their creation times
tmux ls

# Kill sessions for completed projects
tmux kill-session -t old_project

# Kill all sessions (careful!)
tmux kill-server
```

### Scrollback Limits

The default scrollback buffer is 2000 lines, which is often insufficient for bioinformatics output. Increase it in your configuration:

```bash
# In ~/.tmux.conf
set -g history-limit 50000
```

For extremely long outputs, consider redirecting to a file instead of relying on scrollback:

```bash
my_pipeline 2>&1 | tee /data/projects/urine/logs/run_$(date +%Y%m%d).log
```
