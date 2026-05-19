#!/usr/bin/env python3
"""
UserPromptSubmit hook: append every user prompt to ./Prompts/Logs/PROMPT_LOG.md
in the project working directory. Silent on stdout (does NOT inject context).

Skipped when:
  - the cwd has no ./Prompts/ directory (don't pollute non-research projects)
  - the prompt field is empty

Format per entry:
    ## <ISO timestamp>  session=<8-char id>

    ```
    <verbatim prompt text>
    ```
"""
import json, sys, os, datetime

try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)

cwd = d.get("cwd") or os.getcwd()
prompts_dir = os.path.join(cwd, "Prompts")
if not os.path.isdir(prompts_dir):
    sys.exit(0)

prompt = (d.get("prompt") or "").rstrip()
if not prompt:
    sys.exit(0)

logs_dir = os.path.join(prompts_dir, "Logs")
os.makedirs(logs_dir, exist_ok=True)
log_path = os.path.join(logs_dir, "PROMPT_LOG.md")

ts  = datetime.datetime.now().isoformat(timespec="seconds")
sid = (d.get("session_id") or "")[:8]

entry = f"\n## {ts}  session={sid}\n\n```\n{prompt}\n```\n"
with open(log_path, "a") as f:
    f.write(entry)
