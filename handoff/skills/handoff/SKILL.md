---
name: handoff
description: Write or update a terse handoff file capturing the current work, so it's easy to understand and pick up later. Use whenever asked for a handoff or recap. Also use, without writing a file, whenever the ask changes or a dead end arises, to surface it inline as Gotchas.
---

# Handoff

Two modes: the handoff file (explicit ask only) and inline Gotchas (always on, no file).

## Where the file goes

Filename: `<slug>-<latest-edit-date>.md`. Example: `plan-q3-marketing-launch-2026-05-20.md`. Never use a generic name like HANDOFF.md — always use the slug-date pattern.

Location: working directory (outputs folder if one exists) or inline as a code block if you can't write to disk.

Update the filename's date on every write so it always reflects the last edit.

After writing, tell the user the path (use `computer://` links if supported, e.g., Cowork). If you rendered inline, the block itself is the deliverable.

## Format

Use this exact template. Do not substitute free-form notes or a different structure:

```
# <title>

**Goal:** <what we set out to do>

<Two-line prose summary of what happened.>

## Gotchas            (acceptance criteria, constraints, dead ends, takeaways)
- Output must include the per-region breakdown (not in the original brief).
- Use library X v2, not v1; v1 silently drops null fields.
- Tried W, didn't work because V.

## Progress           (ordered list: done, pending, and blockers)
1. [x] Owner: thing that got done
2. [ ] Owner: thing still to do, by <date>
3. [ ] **BLOCKER:** Owner: thing waiting on dependency X

## Questions          (resolved and unresolved)
- [ ] Question?
- [ ] Owner: question?
- [x] Question? -> Answer.
```

Sections below the summary are optional; drop empty ones, don't pad with "None" or filler. Aim for ≤ 5 items per section; if you're over, you're likely restating rules already in this SKILL.md or capturing noise.

## Section taxonomy

Each item in exactly one list; no duplicates.

- **Gotchas** combine key things to know about: acceptance criteria (must-haves that aren't inherently obvious), constraints (required implementation details and settled architecture/approach/formats, with the "why" if it fits), dead ends (approaches that failed and other known pitfalls), and takeaways (high-level lessons assessed at handoff time). Plain bullets, past tense.
- **Progress** covers work items, completed or pending, with named owners. Numbered to make sequence explicit; mark hard blockers with `**BLOCKER:**`.
- **Question** is unresolved or in dispute. Resolved questions stay in Questions (not Gotchas), marked `[x]` with `-> answer`. Optional addressee prefix when someone specific should weigh in.

Signal words like "open", "pending", "TBD", "still to decide" mean a Question, not a Gotcha; a pending choice isn't settled.

If it could be either a Question or a pending Progress item, ask: has someone committed to resolving it with a clear next step? If yes, file as Progress; if no, Question. When in doubt, prefer Question.

## Inline Gotchas

Always on; no ask needed. During any work, when the ask changes or a dead end or pitfall emerges, end that response with a Gotchas list, just before any copyable content:

```
**Gotchas**
- Changes: Goal is a CSV export (was: PDF report).
- New: Tried the bulk API; it caps exports at 10k rows, so paginate.
```

- The ask is the objective (including a topic switch or aside that changes what is being worked on), acceptance criteria, and constraints. It is a subset of context: asides and background facts that leave the ask intact don't qualify unless they create a constraint or dead end.
- Bar: would someone reviewing progress against the original brief need to know this? Routine progress and general facts don't qualify.
- `New:` for a first mention; `Changes:` when revising the brief or an earlier item, with `(was: <prior>)`.
- Only items that arose this turn. Never restate earlier items or the full handoff.
- One line per item; goal changes first.
- Omit the section when nothing qualifies.
- Never write a file.

## Gotchas at handoff time

Build Gotchas from every `New:`/`Changes:` item surfaced inline this session, reconciled against the state at the time of the request:

1. Fold each Change into the item it replaced.
2. Drop items no longer true.
3. Add final high-level takeaways, assessed now.

Drop the `New:`/`Changes:` prefixes; the file is a snapshot. Keep `(was: ...)` only where the prior version would otherwise mislead a reader. If earlier inline items are no longer visible (e.g., after context compaction), reconstruct them from the compaction summary and current state. Existing-file merge rules still apply. The 5-item aim stays soft; surfaced items take priority over new takeaways.

## Updating an existing handoff

Before writing, look for `<slug>-*.md` in the outputs folder (same slug, any date). If found:

1. Read it; treat it as the base.
2. Merge new material across Gotchas, Progress, and Questions. Flip completed progress to `[x]`. Resolve questions with `[x]` and `-> answer`. If the ask changed (goal, acceptance criteria, or constraints), refine the goal and log the change as a Gotcha; context shifts that leave the ask intact aren't Gotchas unless they create a constraint or dead end.
3. Re-date the filename (e.g., `foo-2026-05-20.md` becomes `foo-2026-05-22.md` on May 22).

One handoff file per slug; extend across sessions, never wipe or duplicate.

## When to trigger

Write the file only on explicit ask: "handoff", "recap", "give me the recap", "update the handoff", "what did we cover".

You may offer once after substantive work concludes ("want a recap?"), but never write unprompted.

Exception: Inline Gotchas need no ask and never write a file.

## Style override

If the user includes "freeform" or "free form" in their request, skip the template entirely and write a natural prose summary instead. No prescribed sections — just capture what matters.
