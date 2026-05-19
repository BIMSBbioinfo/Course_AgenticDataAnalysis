#!/usr/bin/env python3
"""
Install the project-scoped auto-logging hooks into existing research projects.

Finds every directory under the given scan roots that contains a `Prompts/`
sub-directory (the marker for a research-setup project), then either installs
or merges `~/.claude/scripts/project-settings-template.json` into
`<project>/.claude/settings.json`.

Default scan roots: ~/Projects ~/Tmp
Override with positional args: install-project-hooks.py /path/one /path/two

Flags:
  --dry-run        show what would change, write nothing
  --max-depth N    how deep to walk under each scan root (default 4)
  --verbose        also list projects that already have the hooks

Merge semantics: if `.claude/settings.json` exists, the script appends our two
hook entries (UserPromptSubmit prompt-log, PostToolUse Bash run-log) to the
relevant arrays without removing or rewriting anything else. Idempotent — runs
multiple times leave the file unchanged after the first.
"""
import argparse, json, os, sys
from pathlib import Path

TEMPLATE_PATH = Path.home() / ".claude" / "scripts" / "project-settings-template.json"
PROMPT_LOG_CMD_FRAGMENT = "prompt-log.py"          # signature of our UPS hook
RUN_LOG_CMD_FRAGMENT    = "RUN_LOG.md"             # signature of our PTU hook


def find_projects(roots, max_depth):
    seen = set()
    for root in roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        root_depth = len(root.parts)
        for dirpath, dirnames, _ in os.walk(root):
            depth = len(Path(dirpath).parts) - root_depth
            if depth > max_depth:
                dirnames[:] = []
                continue
            # don't descend into Prompts/ itself or hidden / vendored dirs
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d not in {"node_modules","renv","Data"}]
            if "Prompts" in dirnames:
                proj = Path(dirpath).resolve()
                if proj not in seen:
                    seen.add(proj)
                    yield proj


def hooks_already_installed(settings):
    ups = settings.get("hooks", {}).get("UserPromptSubmit", [])
    ptu = settings.get("hooks", {}).get("PostToolUse", [])
    has_ups = any(
        PROMPT_LOG_CMD_FRAGMENT in (h.get("command") or "")
        for entry in ups for h in entry.get("hooks", []))
    has_ptu = any(
        RUN_LOG_CMD_FRAGMENT in (h.get("command") or "")
        for entry in ptu for h in entry.get("hooks", []))
    return has_ups, has_ptu


def merge_hooks(existing, template):
    """Append template hooks into existing settings without duplicating."""
    if "hooks" not in existing:
        existing["hooks"] = {}
    for event, entries in template["hooks"].items():
        existing["hooks"].setdefault(event, [])
        for tmpl_entry in entries:
            tmpl_matcher = tmpl_entry.get("matcher", "")
            # find an existing entry with the same matcher, or append a new one
            target = next((e for e in existing["hooks"][event]
                           if e.get("matcher", "") == tmpl_matcher), None)
            if target is None:
                existing["hooks"][event].append(json.loads(json.dumps(tmpl_entry)))
                continue
            target.setdefault("hooks", [])
            existing_cmds = {(h.get("type"), h.get("command")) for h in target["hooks"]}
            for h in tmpl_entry["hooks"]:
                key = (h.get("type"), h.get("command"))
                if key not in existing_cmds:
                    target["hooks"].append(json.loads(json.dumps(h)))
    return existing


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roots", nargs="*", default=[str(Path.home() / "Projects"),
                                                 str(Path.home() / "Tmp")])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-depth", type=int, default=4)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    template = json.loads(TEMPLATE_PATH.read_text())

    n_new = n_merged = n_skipped = 0
    for proj in sorted(find_projects(args.roots, args.max_depth)):
        settings_path = proj / ".claude" / "settings.json"
        if settings_path.exists():
            try:
                existing = json.loads(settings_path.read_text())
            except json.JSONDecodeError as e:
                print(f"  SKIP (malformed JSON): {settings_path}: {e}", file=sys.stderr)
                continue
            has_ups, has_ptu = hooks_already_installed(existing)
            if has_ups and has_ptu:
                if args.verbose:
                    print(f"  ok  {proj}  (already installed)")
                n_skipped += 1
                continue
            merged = merge_hooks(existing, template)
            print(f"  MERGE {proj}  (UPS={'+' if not has_ups else '='}, PTU={'+' if not has_ptu else '='})")
            if not args.dry_run:
                settings_path.write_text(json.dumps(merged, indent=2) + "\n")
            n_merged += 1
        else:
            print(f"  NEW   {proj}")
            if not args.dry_run:
                settings_path.parent.mkdir(parents=True, exist_ok=True)
                settings_path.write_text(json.dumps(template, indent=2) + "\n")
            n_new += 1

    tag = "[dry-run] " if args.dry_run else ""
    print(f"\n{tag}new={n_new}  merged={n_merged}  already-installed={n_skipped}")


if __name__ == "__main__":
    main()
