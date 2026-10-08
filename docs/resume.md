# Tripzy: resume and portfolio wording

## Resume entry (copy-ready)

**Tripzy — Agentic AI Travel Planner | Portfolio project**  
Python, FastAPI, Next.js, React, OpenAI Agents SDK, Gemini, Tavily, Supabase, Docker, Railway, Vercel

- Built and deployed a full-stack AI travel planner that converts natural-language trip requests into persisted workspaces, researched candidates and structured daily itineraries.
- Implemented dependency-driven selective replanning and a save-after-success boundary so revisions rebuild affected artifacts while failed planning preserves the last saved state.
- Established a CI release gate with 115 backend tests, 26 frontend tests, five audit-policy tests, dependency audits and non-root container health checks; measured model behavior across 60 fixed cases with three repeats.

Links: [Live demo](https://tripzy-liard.vercel.app) · [Source](https://github.com/hifzabuildsai/Tripzy) · [89-second video](https://github.com/user-attachments/assets/badc1551-7f3c-4a09-825c-d4b3ef807f50)

## Short portfolio card

Tripzy is a deployed travel-planning portfolio project that combines natural-language interpretation, bounded research and a durable trip workspace. Its engineering focus is deterministic state management: selective revisions, validated itinerary output and persistence only after successful processing. Built with AI-assisted development, with regression tests, repeated model evaluations and documented limitations.

## Optional evaluation bullet

- Evaluated intake and correction extraction plus itinerary invariants over 180 trials with synthetic search replay; retained failures and documented mean exact extraction pass rates of 63.3% (intake) and 90.0% (corrections), rather than claiming universal planning accuracy.

Use this instead of the third resume bullet when the role emphasizes evaluations. The itinerary suite passed tested invariants in 30 trials; complete budget adherence was unmeasured. See the [baseline and methodology](evals.md).

## Claim boundaries

These statements describe a portfolio project, not a commercial service with measured users or business impact. Do not add invented users, bookings, revenue, speedups, savings or latency improvements. The recording speeds up provider waits. Test counts are regression evidence, not model accuracy; the 100% itinerary invariant score is not real-world feasibility. Research candidates can be empty or stale.

Development was AI-assisted with ChatGPT and Codex. Describe the design choices, validation and code you can explain; do not imply development without assistance. No accounts, per-user authorization, purchases, MCP, voice or live timeline were shipped in this portfolio finish.
