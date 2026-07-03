# 2026-06-30 — Project origin

The story of how FilmCortex started, and why it became an AI movie intelligence engine rather than yet another media-request frontend.

## Goal

Build a system that gives users genuinely personal movie recommendations and lets them discover films through natural language, then obtain them with as little friction as possible.

## Context

The starting point was a self-hosted media setup centered on Jellyfin and the ARR stack. The original ambition was to make discovery feel intelligent and conversational rather than list-driven.

The first plan was **not** to build an independent recommendation engine. It was to **fork Jellyfin** and add AI features directly into it:

- AI-powered recommendations
- Natural language movie discovery
- Semantic search
- One-click downloads by talking directly to the ARR stack

The vision was to ask something like:

> "Recommend me slow-burn psychological thrillers with beautiful cinematography."

and have Jellyfin both recommend the titles and trigger their download.

## Context: research phase

Before committing to the Jellyfin fork, we researched the existing ecosystem and found projects that already handle media requesting well, including:

- Seerr / Jellyseerr
- SuggestArr

These already solve the "request media" workflow. That discovery reframed the problem: rebuilding request management would mean re-solving something the community had already solved.

## Decisions made

- **Do not fork Jellyfin.** Forking would couple AI work to a large, general-purpose media server and pull us into maintaining features (playback, libraries, request flows) that are not our differentiator.
- **Do not rebuild request/download management.** Integrate with the existing ARR ecosystem instead of replacing Seerr/Jellyseerr/SuggestArr.
- **Focus on the unsolved problem: high-quality personalized recommendations.** Make deep, semantic understanding of taste the core of the product.
- **Build FilmCortex as an independent AI engine** that other tools (Jellyfin, ARR) can integrate with, rather than a feature bolted onto one of them.

## Alternatives considered

- **Fork Jellyfin and embed AI features (original plan).** Rejected: large surface area, heavy maintenance burden, and it entangles our differentiator with an existing codebase's constraints.
- **Build another request frontend.** Rejected: the request workflow is already a solved problem; adding one more would provide little new value.
- **Rely on existing recommendation approaches** (trending, popularity, recently-watched, basic collaborative filtering, static recommendation APIs). Rejected: none of these feel genuinely personal. Even importing a Letterboxd watchlist or using recent viewing history fails to capture *why* a person enjoyed a film.

## What changed

This was the major architectural pivot. Instead of becoming another request frontend, FilmCortex became an **AI movie intelligence engine** whose responsibilities are to:

- understand movies
- understand users
- generate high-quality recommendations
- create meaningful collections
- power semantic search

Requesting and downloading media integrates with the existing ARR ecosystem rather than replacing it. The core differentiator is **AI understanding and recommendation**, not media downloading.

## Verification

This entry documents a direction/strategy decision rather than a code change, so validation was qualitative:

- Confirmed that the request workflow is well covered by existing tools (Seerr/Jellyseerr, SuggestArr).
- Confirmed that deep, taste-level personalization is not well served by current popularity- and history-based approaches.

The decision is considered validated because it concentrates effort on the genuinely unsolved problem and avoids duplicating solved ones.

## Lessons learned

- Survey the ecosystem before building: the best scope is often defined by what is *not* yet solved.
- Differentiate on the hard, unsolved problem (personalization) instead of re-implementing commodity workflows (requesting/downloading).
- Staying independent and integration-friendly keeps the project focused and avoids inheriting another project's maintenance burden.

## Next steps

- Establish the ingestion → PostgreSQL → offline jobs → API pipeline as the backbone (see [architecture.md](../architecture.md)).
- Build the embedding pipeline as the foundation for semantic understanding (see [roadmap.md](../roadmap.md)).
- Design taste modeling and recommendation generation on top of embeddings.
- Integrate with the ARR stack for the request/download hand-off.
