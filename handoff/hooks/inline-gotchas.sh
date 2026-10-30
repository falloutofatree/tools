#!/bin/sh
# SessionStart: put the skill's "Inline Gotchas" section in context so the rule
# applies without invoking the skill. SKILL.md is the single source; edit it there.
skill="${CLAUDE_PLUGIN_ROOT}/skills/handoff/SKILL.md"
rule=$(awk '/^## Inline Gotchas/{f=1; next} /^## /{f=0} f' "$skill")
[ -n "$rule" ] || { echo "handoff: Inline Gotchas section not found in $skill" >&2; exit 1; }
printf 'Handoff plugin rule, Inline Gotchas (always on):\n%s\n' "$rule"
