# handoff `v2.0.0 · 2026-10-30`

Structured handoffs, plus inline Gotchas as the work changes, so it's easy to see what changed and pick the work up later.

## Why

Reviewing progress on a piece of work usually means starting from the brief (objectives, acceptance criteria, constraints) and scanning forward for anything that changed it. This plugin does a little of that scanning for you: it flags changes to the ask as they happen, and folds them into a structured handoff when you ask for one.

It's a light assist for clarity, not an audit log. It doesn't record everything Claude read or did, it isn't exhaustive or even thorough, and it can be wrong or miss things. Treat a Gotcha as a pointer to look closer, not as a record.

## Handoffs

Run the `handoff` skill with `/handoff`, or ask in natural language, like "give me a recap," "what did we cover," or "update the handoff." The skill may offer once when substantive work concludes but never writes unprompted.

The output is a structured `<slug>-<latest-edit-date>.md` file (never a generic name like `HANDOFF.md`) with:

- A goal and two-line summary.
- Gotchas: the items surfaced inline during the session, checked against the current state, plus final takeaways.
- Progress (ordered list of done, pending, and blockers).
- Questions (resolved and unresolved).

If a handoff file already exists for the same slug, the skill extends it (and re-dates the filename). Falls back to inline rendering as a code block if it can't write to disk.

If the request includes "freeform" or "free form", the structured template is skipped and the output is a natural prose summary instead.

## Inline Gotchas

An incremental recap. Each Gotcha appears in the turn where it arose, next to the work it's connected to, so you see the change in context instead of reconstructing it at the end. A response ends with a short list, just before any copyable content:

```
**Gotchas**
- Changes: Goal is a CSV export (was: PDF report).
- New: The bulk API caps exports at 10k rows, so paginate.
```

Only items from that turn appear; earlier items aren't repeated, nothing appears when nothing qualifies, and no file is written.

### What triggers a Gotcha

A Gotcha appears only when something changes the ask or how it will be done:

- **Ask:** objectives, scope, acceptance criteria, or other constraints.
- **Topic:** a switch of topic, including an aside, when it changes what's being worked on.
- **Blocks and unblocks:** a dead end, a pitfall, or a lifted blocker, when it changes the ask or the approach.
- **Context:** a change of repo or directory, a new task, or a subagent's result, when it changes the ask or the approach. Context changes that leave the ask intact aren't surfaced yet (see Future).

Routine progress and background facts don't qualify. The test: would someone reviewing progress against the original brief need to know this?

### When the rule loads

A SessionStart hook loads the rule from the skill at session start, `/clear`, resume, and compaction, so it applies without invoking the skill. These events reload the rule; they don't produce Gotchas on their own.

Hooks run in Claude Code and Cowork (not yet verified in Cowork) but are ignored in chat. In chat, inline Gotchas rely on the skill description alone, which is less reliable: it didn't fire on Haiku in testing. To cover chat, add a one-line Gotchas rule to your preferences.

## Future

- Surface context changes beyond the ask, such as background facts, the environment, discoveries, and asides.
- Check for and resolve conflicts between this skill's instructions and other user preferences and skills.
- Briefly document what the "ask" should contain for best Gotcha capture.
- An easy way to collect handoffs centrally, in addition to saving them in the session or working folder.
- Slim down or retire this plugin if AI tools ship structured, incremental recaps natively. As of this writing, built-in recaps and handoffs exist but are ad hoc rather than structured like this.
