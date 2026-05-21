---
name: handoff
description: Write or update a terse handoff file capturing the current work, so it's easy to understand and pick up later. Use whenever asked for a handoff or recap.
---

# Handoff

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

## Gotchas            (acceptance criteria, constraints, dead ends)
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

- **Gotchas** combine key things to know about: acceptance criteria (must-haves that aren't inherently obvious), constraints (required implementation details and settled architecture/approach/formats, with the "why" if it fits), and dead ends (approaches that failed and other known pitfalls). Plain bullets, past tense.
- **Progress** covers work items, completed or pending, with named owners. Numbered to make sequence explicit; mark hard blockers with `**BLOCKER:**`.
- **Question** is unresolved or in dispute. Resolved questions stay in Questions (not Gotchas), marked `[x]` with `-> answer`. Optional addressee prefix when someone specific should weigh in.

Signal words like "open", "pending", "TBD", "still to decide" mean a Question, not a Gotcha; a pending choice isn't settled.

If it could be either a Question or a pending Progress item, ask: has someone committed to resolving it with a clear next step? If yes, file as Progress; if no, Question. When in doubt, prefer Question.

## Updating an existing handoff

Before writing, look for `<slug>-*.md` in the outputs folder (same slug, any date). If found:

1. Read it; treat it as the base.
2. Merge new material across Gotchas, Progress, and Questions. Flip completed progress to `[x]`. Resolve questions with `[x]` and `-> answer`. If scope shifted, refine the goal and log the shift as a Gotcha.
3. Re-date the filename (e.g., `foo-2026-05-20.md` becomes `foo-2026-05-22.md` on May 22).

One handoff file per slug; extend across sessions, never wipe or duplicate.

## When to trigger

Only on explicit ask: "handoff", "recap", "give me the recap", "update the handoff", "what did we cover".

You may offer once after substantive work concludes ("want a recap?"), but never write unprompted.

## Style override

If the user includes "freeform" or "free form" in their request, skip the template entirely and write a natural prose summary instead. No prescribed sections — just capture what matters.
