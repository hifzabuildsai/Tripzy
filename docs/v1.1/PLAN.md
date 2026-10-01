# Tripzy v1.1 — Milestone Plan (M19)

**Baseline:** `v1.0.0` (`1a3345b`), `main` at `3b93020` (docs-only after tag).
**Goal:** make Tripzy visibly agentic and usable in any language, by voice or
text, with evals that prove the LLM boundary works.
**Out of scope:** landing-page redesign, 3D, real-time duplex voice, TTS,
auth/accounts, bookings/inventory, UI-chrome translation, multi-replica.

## Order and dependencies

```text
M19.0 Bootstrap ──► M19.1 Evals ──► M19.2 Any-language ──► M19.3 Push-to-talk ──► M19.4 Live timeline ──► M19.5 Release
                     (measure)       (needs evals)          (needs M19.2)           (needs M19.1 seam)
```

- Evals first: every later milestone changes prompts or the run path. A
  baseline is required to prove nothing regressed (the M18.3 `interests_replace`
  bug was exactly an unmeasured LLM-boundary failure).
- Multilingual before voice: an Urdu transcript is useless if replies are English-only.
- Timeline last: it is the riskiest refactor (blocking request → background run)
  and touches the failure-safe invariant; evals and tests guard it by then.

Each milestone = one branch + one PR, merged by Hifza before the next starts.

---

## M19.0 — Bootstrap

**Goal:** put the rules and plan in the repo; lock the contracts before code.

**Prerequisites (Hifza, manual):**
- Railway → `tripzy-api` → Settings → Source: fix "Auto deploy unavailable /
  Could not load branches" (GitHub → Settings → Applications → Railway →
  Configure → grant `hifzabuildsai/Tripzy`). Confirm the active deployment
  commit is ≥ `f032bd7`.
- GitHub → repo Settings → Secrets → Actions: add `GEMINI_API_KEY` (and
  `TAVILY_API_KEY` for fixture recording) for the on-demand eval workflow.

**Build:**
- Add `AGENTS.md` (root) and `docs/v1.1/PLAN.md`.
- Write `docs/v1.1/CONTRACTS.md` with four contracts, derived from this plan and
  the current code:
  1. Eval case schema (JSONL fields per suite) and report schema.
  2. Language contract (`response_language` storage, canonicalization rules,
     localization guard rules, fallback).
  3. `POST /transcribe` API (request, limits, response, errors).
  4. Run-event schema v1 (event types, payloads, SSE framing, reconnect).

**Acceptance:** PR with docs only; zero app-code changes; CI green.
**Non-goals:** any implementation.

---

## M19.1 — Eval harness + baseline

**Goal:** measure the LLM boundary in English and other languages, offline-repeatable.

**Build:**
1. **Single search seam.** Today four modules instantiate `TavilyClient`
   directly (`travel_search.py`, `flight_search.py`, `hotel_search.py`,
   `activity_search.py`). Route all calls through one function (e.g.
   `app/tools/search_client.py::search(...)`) with `TRIPZY_SEARCH_MODE` =
   `live` (default, production unchanged) | `record` | `replay`.
   Replay reads fixtures keyed by a stable hash of (query, params); a missing
   fixture in replay mode raises, never silently goes live.
   Exclude `evals/` from the Docker image (`.dockerignore`).
2. **`evals/` package:**
   - `datasets/*.jsonl`, `fixtures/search/`, `graders/`, `run.py`,
     `reports/` (gitignored except baselines), `baselines/`.
   - Runner: `python -m evals.run --suite <name|all> --search-mode replay
     [--repeat N] [--concurrency 2]`, with retry/backoff for Gemini rate
     limits. Writes JSON + a Markdown summary (mean, min across repeats,
     per-case failures).
3. **Suites (programmatic graders; LLM-judge only where noted):**

   | Suite | Cases | Input → expected | Metrics |
   |---|---|---|---|
   | `intake_extraction` | ~40 | message(s) → `TripRequest` field subset | field precision/recall; **unrequested-field rate** |
   | `correction_extraction` | ~60 | current request + utterance → `TripCorrection` | exact-match; **unrequested-field rate** (target ≤ 2%); interest-op correctness; must include the budget-only `interests_replace: []` regression |
   | `itinerary_invariants` | ~10 trips (replay) | full run → itinerary | days == `duration_days`; dates contiguous and inside range; every activity maps to a researched candidate; budget adherence where costs are exposed |

   **≥ 30% of intake/correction cases multilingual:** Urdu script, Roman Urdu,
   code-switched Urdu–English, Arabic, Hindi, Turkish, Spanish. Expected values
   stay canonical (see M19.2), e.g. "استنبول" → `Istanbul`, "khana" → `food`.
4. **CI:** `.github/workflows/evals.yml`, `workflow_dispatch` only, replay
   mode, uploads the report as an artifact. Not part of the release gate.
5. **pytest:** unit tests for the search seam (live/record/replay switching,
   missing-fixture error) and each grader. No network in pytest.

**Acceptance:**
- Existing pytest suite green + new tests green; release gate green.
- `evals/baselines/v1.0.0.json` committed (`--repeat 3`).
- PR description has the baseline table, with multilingual failures listed
  (expected: many; this milestone measures, it does not fix).

**Non-goals:** changing any prompt, model, or agent behavior.

---

## M19.2 — Any-language agent

**Goal:** a user can write in any language (incl. Roman Urdu / code-switching)
and Tripzy replies in that language, without weakening deterministic state.

**Build:**
1. **Language state.** Add `response_language: str` (BCP-47, default `"en"`)
   to `TripState`, **not** to `TripRequest`. A language change is not a trip
   change: it must never appear in `changed_fields` or invalidate artifacts.
2. **Detection.** The intake (`extract_trip_request`) and correction
   (`extract_trip_correction`) tools also return `user_language`. Python
   updates `response_language` every turn (users may switch languages).
   Missing or invalid → keep the previous value.
3. **Canonical state.** Update the extraction prompts: input may be any
   language or script. Output stays canonical: place names as standard English
   names, interests as lowercase English keys, dates through the existing
   deterministic date semantics (`date_semantics.py`). Research queries stay
   English (better Tavily recall).
4. **Localization layer** `app/services/localization.py`:
   - `localize(text, lang) -> str`. `lang == "en"` → passthrough, no LLM call.
   - Otherwise the LLM translates with strict rules: translate only, add no
     facts, keep Western digits, currency codes, dates, URLs, and IATA codes as-is.
   - **Guard (code):** extract protected tokens (numbers, amounts, ISO dates,
     URLs, codes) from the source; every one must appear in the output. On
     guard failure or timeout (~20 s, inside the 240 s budget) → return the
     English source and log `localization_fallback` (redacted).
   - Apply to user-facing text: `TripManager.get_next_question`, the
     combined planning response, revision acknowledgements, user-facing errors.
5. **Frontend (minimal, M15-safe):** `dir="auto"` and `lang` on message
   bubbles; add a Nastaliq/Naskh-capable font via `next/font` scoped to those
   scripts. No other visual change. UI chrome stays English.
6. **Evals:** new `localization` suite (fact-preservation rate before the guard;
   language-match rate via script check for ur/ar/hi; LLM-judge only for
   Roman-Urdu-vs-English); rerun all suites.

**Acceptance:**
- Multilingual intake/correction scores within 5 points of the English
  baseline; English scores do not regress beyond `--repeat 3` noise.
- Unit tests: guard pass/fail/fallback; a language switch never invalidates artifacts.
- Release gate green; PR includes the before/after eval table.

**Non-goals:** translating stored research data; UI-chrome i18n; per-user settings.

---

## M19.3 — Push-to-talk

**Goal:** speak instead of typing, in any language; the transcript is reviewed
before sending.

**Build:**
1. **Frontend `VoiceInputButton`** in `TripComposer` and `TripRevisionPanel`:
   - `MediaRecorder`: `audio/webm;codecs=opus`, `audio/mp4` fallback for Safari.
   - Tap to start, tap to stop; auto-stop at 45 s; recording timer.
   - States: idle / recording / transcribing / error / permission-denied.
   - Keyboard-operable, visible focus, honors reduced motion.
   - **The transcript is inserted into the text box. It never auto-submits.**
2. **Backend `POST /transcribe`** (multipart):
   - Its own size cap (~1.5 MB), exempt from the 16 KiB JSON limit for this
     route only. Content-type allowlist (webm/ogg/mp4/mpeg/wav).
   - Rate-limited, counted in the same per-client limiter or its own 10/min.
   - Audio is never persisted and never logged.
   - Returns `{text, language}`.
3. **Transcription:** Gemini audio input. First verify whether Gemini's
   OpenAI-compatible endpoint accepts audio; if not, use the native Gemini SDK
   for this one call only (add it to `requirements.lock` with hashes; must
   pass pip-audit). Report which path was chosen and why.
4. **Tests:** backend tests with a mocked transcriber (413 oversize, 415 bad
   type, 429 rate limit, happy path, audio never written to disk/logs); Vitest
   for the button state machine with a mocked `MediaRecorder`.

**Acceptance:**
- Release gate green.
- Manual QA on Chrome desktop, Android Chrome, iOS Safari in English, Urdu
  and Roman-Urdu-style speech; results table in the PR.
- If the frontend sets any `Permissions-Policy`, it allows `microphone=(self)`.

**Non-goals:** real-time conversation, wake words, text-to-speech, streaming STT.

---

## M19.4 — Live agent timeline (runs + SSE)

**Goal:** the user watches the agent work: stages, searches, sources,
artifacts, and what replanning kept versus reran.

**Build:**
1. **`RunManager`** (process-local, single replica): `run_id` → asyncio
   task + ordered event log + subscriber queues. TTL cleanup ~15 min after
   the run ends.
2. **API:**
   - `POST /trips/{trip_id}/runs {message}` → 202 `{run_id}`. Overload → 503
     *before* 202. Rate limit and message limits apply here.
   - `GET /trips/{trip_id}/runs/{run_id}/events` → SSE: `id:` per event,
     `Last-Event-ID` replay, heartbeat comment every 15 s, closes after the
     terminal event.
   - `GET /trips/{trip_id}` includes `active_run_id` while a run is live, so
     a refresh can reattach.
   - Keep `POST /trips/{trip_id}/messages` working (backward compatible).
3. **Events (Pydantic, `v: 1`):** `run_started`, `stage_started{stage}`,
   `tool_call{tool, query}`, `source_found{stage, title, url}`,
   `artifact_ready{kind, count, preview[]}`,
   `replan_plan{changed_fields, rerun[], kept[]}`,
   `stage_completed{stage, duration_ms}`, `message{text}` (localized),
   `run_completed`, `run_failed{reason, preserved_previous: true}`.
   Emit from the existing stage boundaries in `conversation.py`, the M19.1
   search seam, and `invalidated_artifacts()`. No secrets or trip IDs in payloads.
4. **Invariants preserved:** the concurrency guard (2), 1 s queue and 240 s
   timeout wrap the background task; persist only on `run_completed`; timeout
   or failure emits `run_failed` and the stored plan is untouched.
5. **Frontend `RunTimeline`** replaces the "Tripzy is planning your trip…"
   screen:
   - 5 stages with pending / running / done / kept states, live query list,
     sources, preview cards on `artifact_ready`.
   - On a replan, kept stages show "kept ✓" immediately.
   - The composer transitions into the timeline using the existing `lib/motion`.
   - Event-to-UI logic is a pure reducer (unit-testable).
   - Reattaches on refresh via `active_run_id`.
6. **Tests:** RunManager (ordering, replay from `Last-Event-ID`, TTL,
   failure preserves state, timeout path, overload), SSE via TestClient
   streaming, Vitest for the reducer.

**Acceptance:**
- Release gate green.
- Live production: a full run is visible end to end; a budget correction
  shows kept vs rerun stages; a forced model failure shows `run_failed` and the
  previous plan survives refresh; a mid-run refresh reattaches; SSE survives the
  Railway proxy for a full 240 s run.

**Non-goals:** mid-run steering or cancel (log as a v1.2 idea), multi-replica fan-out.

---

## M19.5 — Release v1.1

**Build / verify:**
- All M19 PRs merged; CI green on final `main`.
- Railway auto-deploy confirmed at the final `main` SHA; Vercel production at `main`.
- Live QA matrix:
  - English, Urdu-script and Roman-Urdu trips
  - Voice in two languages
  - Selective replan with the timeline
  - Forced failure
  - `/transcribe` limits
  - Security headers and docs-disabled checks unchanged
- `python -m evals.run --suite all --repeat 3` on final `main` →
  `evals/baselines/v1.1.0.json`.
- README:
  - "Evals" section with the v1.0.0 → v1.1.0 score table
  - Multilingual and voice in features
  - Updated architecture note (runs + SSE)
  - New 90-second demo link
- Tag `v1.1.0`; GitHub Release with notes.

**Acceptance:** production = `main` = `v1.1.0`; release evidence in the PR/Release notes.
