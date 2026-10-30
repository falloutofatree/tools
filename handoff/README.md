# handoff `v1.1.0 · 2026-10-30`

Write or update a terse handoff file capturing the current work, so it's easy to understand and pick up later.

## What it does

Adds two slash commands:

- `/handoff` (or `/recap`) - write or update the handoff for the current work.

Also bundles a `handoff` skill that triggers on natural-language asks like "give me a recap," "what did we cover," or "update the handoff." The skill may offer once when substantive work concludes but never writes unprompted.

Inline Gotchas are always on: when the ask (goal, acceptance criteria, constraints) changes or a dead end arises, the response ends with a short **Gotchas** list of `New:` and `Changes:` items from that turn only. No file is written. Best effort: this relies on Claude acting on the skill description, not a hook.

The output is a structured `<slug>-<latest-edit-date>.md` file (never a generic name like `HANDOFF.md`) with:

- A goal and two-line summary.
- Gotchas (acceptance criteria, constraints, dead ends): the items surfaced inline, reconciled, plus final takeaways.
- Progress (ordered list of done, pending, and blockers).
- Questions (resolved and unresolved).

If a handoff file already exists for the same slug, the skill extends it (and re-dates the filename). Falls back to inline rendering as a code block if it can't write to disk.

If the request includes "freeform" or "free form", the structured template is skipped and the output is a natural prose summary instead.
