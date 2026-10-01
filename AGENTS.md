# Tripzy — agent rules (AGENTS.md)

These rules apply to any coding agent working on this repo (ChatGPT Work, Codex, Claude Code).

Tripzy is a production agentic AI travel planner. v1.0.0 is released and live.
Current scope: **v1.1 (milestones M19.0–M19.5)**, defined in `docs/v1.1/PLAN.md`.
Read that file before doing anything. Do only the milestone you were asked to do.

## History (you have no memory of it; the repo is the source of truth)

Tripzy was built from scratch by Hifza with ChatGPT and Codex across
milestones M1–M18 (Sept–Oct 2026). v1.1 continues with the same agents.
- M1–M14: agents, structured request/state, deterministic dates, research
  stages, itinerary, FastAPI + Supabase, backend hardening.
- M15: frontend ("conversation inside a travel dream", sticker world). Locked.
- M16A/B: durable sessions and routing; selective replanning; failure-safe retry. Locked.
- M17: Docker/Railway/Vercel production deployment. Locked.
- M18.1–18.5: CI release gate, sticker hit-test fix, public-demo hardening,
  production QA (PR #4 fixed the `interests_replace: []` regression),
  portfolio README, release `v1.0.0` (PRs #1–#10).
- Live: frontend https://tripzy-liard.vercel.app · API
  https://tripzy-api-production.up.railway.app/health

Follow the existing code's patterns and naming. Don't restyle or "modernize"
code you weren't asked to touch.

## Architecture (frozen)

- LLMs interpret and reason. **Deterministic Python owns application truth**:
  state, workflow, validation, persistence, invariants.
- Backend: FastAPI (`app/`), OpenAI Agents SDK over Gemini's OpenAI-compatible
  endpoint (`app/config.py`), Tavily search (`app/tools/`), Supabase via the
  `TripRepository` abstraction (`app/services/trip_repository.py`).
- Frontend: Next.js 16 / React 19 / Tailwind 4 / Motion (`frontend/`).
- Production: Vercel (frontend), Railway Docker single replica (backend),
  Supabase Postgres. Gemini + Tavily keys are backend-only.

## Locked invariants — never weaken

1. **Selective replanning:** a correction changes only the fields the user
   explicitly changed; only dependent artifacts are invalidated
   (`app/services/replanning.py`). An empty `interests_replace` is "not provided".
2. **Failure-safe persistence:** planning works on a copy; persist only on full
   success. Failure, timeout or overload never overwrites the previous plan.
3. **Research results are candidates**, never bookings or guaranteed availability.
4. **The itinerary planner consumes structured research**; it never performs
   new research itself.
5. **M18.2 hardening stays:** 16 KiB JSON body limit, 4,000-char message limit,
   20 writes/60 s per client, max 2 concurrent planning jobs, 1 s queue,
   240 s timeout, redacted logging, prod docs/OpenAPI disabled, security headers,
   exact-origin CORS. New endpoints get their own explicit limits.
6. **M15 visual system is frozen.** No redesign of the landing page, sticker
   world, palette or layout. New UI must fit the existing system.
7. **Process-local state assumes one Railway replica.** Document any new
   process-local state.

## Security

- Never print, log, echo or commit secret values. Refer to variable names only.
- Never commit `.env`. Never put Gemini/Tavily/Supabase secrets in `frontend/`.
- Never log raw user audio, trip IDs in access logs, or full prompts in production.

## Working rules

- One milestone per session. Branch: `m19-<n>-<slug>` from latest `origin/main`.
- Start every milestone with inspection and a written plan. Wait for
  approval before editing anything.
- Evidence before edits. Smallest change that meets the acceptance criteria.
  No speculative refactors, no scope creep, no drive-by "improvements".
- Never `git reset --hard`, `git clean`, force-push, rewrite history, or delete
  files you did not create. Inspect `git status` first; preserve unknown local
  files (e.g. `conversation-current.txt`, `*.patch`, `frontend/next-env.d.ts`).
- **Push work in progress early and often.** After plan approval, commit and
  push to the milestone branch after every sub-step that passes its tests
  (`wip:` commits are fine and get squashed at merge). A session that dies
  must lose nothing; in M18.3 an interrupted session lost an unpushed fix.
- Never merge PRs. Open the PR, wait for CI, report, stop.
- Commit messages: conventional style (`feat:`, `fix:`, `test:`, `docs:`, `ci:`).

## Release gate (run locally before opening a PR)

```bash
# backend
pytest -q
python -m pip_audit --requirement requirements.lock
# frontend
cd frontend && npm ci && npm audit --audit-level=high && npm test && npm run lint && npm run build && cd ..
# container
docker build --tag tripzy-backend:release-gate .
```

CI (`.github/workflows/ci.yml`) runs the same plus Gitleaks, non-root checks
and a container `/health` smoke test. A PR is not done until CI is green.

## Evals (from M19.1 onward)

```bash
python -m evals.run --suite all --search-mode replay            # standard
python -m evals.run --suite correction_extraction --repeat 3    # variance check
```

Evals call Gemini (cost + rate limits). Never add them to the PR release gate.
If your sandbox cannot reach Gemini or Tavily, say so plainly and give Hifza the
exact command to run on her own machine; she will paste the report back.
Any change to a prompt or extraction tool must include a before/after eval
report in the PR description.

## Milestone report format (end of every session)

starting SHA · branch · final commit · files changed · what was built ·
tests added + results · release gate results · eval results (if applicable) ·
PR URL · CI status · deviations from PLAN.md · open questions · next milestone.
