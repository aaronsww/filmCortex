# FilmCortex Devlog

This is the engineering journal for FilmCortex. Its purpose is to preserve the **journey** of the project — the reasoning, trade-offs, and pivots — not just the final architecture. Months or years from now, someone should be able to read these entries and understand *why* the system looks the way it does.

## When to write an entry

Create a new entry for every **significant milestone or architectural pivot**, for example:

- a major direction change (a project pivot)
- introducing or replacing a core component (database, ingestion, embedding pipeline, API surface)
- a non-obvious design decision worth remembering
- a milestone that changes how the system is built or operated

Small, routine changes do not need an entry. Use the [roadmap](../roadmap.md) to track granular progress; use the devlog to capture the story behind the notable moments.

## File naming

One markdown file per entry, named:

```
YYYY-MM-DD-short-slug.md
```

Example: `2026-06-30-project-origin.md`. Entries are ordered chronologically by date prefix.

## Entry template

Each entry should include the following sections (omit a section only if it genuinely does not apply):

- **Goal** — what we set out to achieve.
- **Context** — the situation and constraints at the time.
- **Decisions made** — what we chose to do.
- **Alternatives considered** — options we evaluated and why we rejected them.
- **What changed** — the concrete changes (code, schema, architecture, direction).
- **Verification** — how we confirmed it works / how we validated the decision.
- **Lessons learned** — insights worth carrying forward.
- **Next steps** — what this unlocks or what follows.

## Entries

- [2026-06-30 — Project origin](2026-06-30-project-origin.md)
