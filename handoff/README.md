# handoff `v2.0.0 · 2026-10-30`

Write or update a terse handoff file capturing the current work, so it's easy to understand and pick up later.

## What it does

Bundles a `handoff` skill. Run it with `/handoff`, or ask in natural language, like "give me a recap," "what did we cover," or "update the handoff." The skill may offer once when substantive work concludes but never writes unprompted.

Inline Gotchas are always on: when the ask (goal, acceptance criteria, constraints) changes or a dead end arises, the response ends with a short **Gotchas** list of `New:` and `Changes:` items from that turn only. No file is written. A SessionStart hook loads this rule from the skill at startup, resume, `/clear`, and compaction, so it applies without invoking the skill.

The output is a structured `<slug>-<latest-edit-date>.md` file (never a generic name like `HANDOFF.md`) with:

- A goal and two-line summary.
- Gotchas (acceptance criteria, constraints, dead ends): the items surfaced inline, reconciled, plus final takeaways.
- Progress (ordered list of done, pending, and blockers).
- Questions (resolved and unresolved).

If a handoff file already exists for the same slug, the skill extends it (and re-dates the filename). Falls back to inline rendering as a code block if it can't write to disk.

If the request includes "freeform" or "free form", the structured template is skipped and the output is a natural prose summary instead.

## Future

- Surface context changes beyond the ask, such as background facts, the environment, discoveries, and asides.
- Check for and resolve conflicts between this skill's instructions and other user preferences and skills.
- Briefly document what the "ask" should contain for best Gotcha capture.
