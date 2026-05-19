#!/usr/bin/env bash
# Claude Code status line script
# Placed at /home/vfranke/.claude/statusline.sh
# Reads JSON from stdin and prints a one-line status

input=$(cat)

# Parse all fields with python (jq isn't installed). Tab-separated output;
# empty fields become "_" sentinel so positional parsing stays aligned.
parsed=$(STATUSLINE_JSON="$input" python3 <<'PY'
import json, os
d = json.loads(os.environ["STATUSLINE_JSON"])
def g(*path, default=""):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return "" if cur is None else cur
fields = [
    g("model", "display_name", default="unknown model"),
    g("cwd") or g("workspace", "current_dir"),
    g("context_window", "used_percentage"),
    g("context_window", "total_input_tokens"),
    g("context_window", "context_window_size"),
    g("rate_limits", "five_hour", "used_percentage"),
    g("rate_limits", "seven_day", "used_percentage"),
    g("vim", "mode"),
]
print("\t".join("_" if f == "" else str(f) for f in fields))
PY
)

IFS=$'\t' read -r model cwd used_pct total_input ctx_size five_h seven_d vim_mode <<<"$parsed"

# Convert "_" sentinel back to empty
for v in model cwd used_pct total_input ctx_size five_h seven_d vim_mode; do
    [ "${!v}" = "_" ] && printf -v "$v" '%s' ''
done

# Shorten cwd with ~
home="${HOME:-/home/vfranke}"
cwd="${cwd/#$home/\~}"

# Build output with ANSI colors
SEP="\033[2m │ \033[0m"

out="\033[36m${model}\033[0m"

if [ -n "$cwd" ]; then
    out="${out}${SEP}\033[33m${cwd}\033[0m"
fi

# Context usage segment
if [ -n "$used_pct" ] && [ -n "$ctx_size" ] && [ -n "$total_input" ]; then
    used_fmt=$(printf "%.0f" "$used_pct")
    tok_k=$(awk "BEGIN { printf \"%.1fk\", $total_input/1000 }")
    ctx_k=$(awk "BEGIN { printf \"%.0fk\", $ctx_size/1000 }")
    if   [ "$used_fmt" -ge 80 ] 2>/dev/null; then color="\033[31m"
    elif [ "$used_fmt" -ge 50 ] 2>/dev/null; then color="\033[33m"
    else                                          color="\033[32m"
    fi
    out="${out}${SEP}${color}ctx: ${tok_k}/${ctx_k} (${used_fmt}%)\033[0m"
elif [ -n "$used_pct" ]; then
    used_fmt=$(printf "%.0f" "$used_pct")
    out="${out}${SEP}\033[32mctx: ${used_fmt}%\033[0m"
fi

# Rate limits
rate_str=""
if [ -n "$five_h" ]; then
    rate_str="${rate_str}5h:$(printf '%.0f' "$five_h")%"
fi
if [ -n "$seven_d" ]; then
    [ -n "$rate_str" ] && rate_str="${rate_str} "
    rate_str="${rate_str}7d:$(printf '%.0f' "$seven_d")%"
fi
if [ -n "$rate_str" ]; then
    out="${out}${SEP}\033[35m${rate_str}\033[0m"
fi

if [ -n "$vim_mode" ]; then
    out="${out}${SEP}\033[1;34m${vim_mode}\033[0m"
fi

printf '%b\n' "$out"
