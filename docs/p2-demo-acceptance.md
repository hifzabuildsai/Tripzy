# P2: shipped demo acceptance

Verified October 8, 2026 (Asia/Karachi), after PR #12 merged.
Scope: the portfolio P2 checklist in `docs/evals.md`; no feature expansion.
Starting commit: `287a355848608391083be5050eef5494d376d3d7`.
Branch: `m19-2-demo-qa`.

## Approved verification plan

1. Confirm the merged source, release gate, and production deployment records.
2. Exercise a fresh complete mission and a separate incomplete mission.
3. Verify persisted state through refresh, direct links, and navigation.
4. Compare canonical state before/after a narrow budget correction.
5. Inspect desktop and mobile layouts, candidate/source presentation, and a
   missing-trip recovery path. Use existing controlled regressions for planning
   failure and retry; never deliberately break production.
6. Record evidence and limitations. Make only fixes supported by observed bugs.

## Deployment evidence

Frontend: https://tripzy-liard.vercel.app
API: https://tripzy-api-production.up.railway.app

GitHub deployment records:

| Service | Deployment | Source | Result |
| --- | --- | --- | --- |
| Vercel Production | 6925366368 | `287a355848608391083be5050eef5494d376d3d7` | success, October 8 at 02:00:33 UTC |
| Railway Tripzy / production | 6925358505 | `287a355848608391083be5050eef5494d376d3d7` | success, October 8 at 02:00:53 UTC |
| Previous Railway release | 6925371654 | `1a3345b99c97be4371e61edca3910a791cdb4bad` | inactive |

The [merged-main release gate](https://github.com/hifzabuildsai/Tripzy/actions/runs/37715671838)
passed. Deployment-source claims use provider-written GitHub records, not a
version inferred from HTML or `/health`. Neither public endpoint attests its
running Git SHA; deployment records plus successful live behavior are the
available evidence. No hosting configuration or production credentials changed.

## Acceptance matrix

| Check | Method and observed result | Verdict |
| --- | --- | --- |
| Complete mission | Fresh browser trip: Karachi to Istanbul, September 10, 2027, five days, two travelers, USD 2,000, history/food, relaxed. Canonical state reached `itinerary_planned`; three flight candidates, five hotels, eight activities, four destination sources, five itinerary days September 10-14. | Pass |
| Clarification | Separate fresh trip: “I want to visit Seoul for food and museums.” UI listed origin, start date/year, duration/end, travelers, budget/currency as missing. No research artifacts were shown. | Pass |
| Partial clarification | “I'm traveling from Lahore.” updated the same trip to Lahore → Seoul, kept food/museums and requested the remaining fields. Refresh restored this collecting state. | Pass |
| Refresh | Reloaded the completed itinerary route; the same five-day persisted itinerary restored. Revised brief displayed USD 2,500 with history/food and relaxed pace. | Pass |
| Direct link | Opened the completed itinerary URL in the separate mobile tab; same saved itinerary restored without another mission submission. | Pass |
| Workspace views | Brief, Discover, Options and Itinerary navigation worked; Discover exposed destination source links and eight activities; Options exposed flight/hotel candidates. | Pass |
| Budget-only replan | “Change only the total budget to $2,500 USD.” kept the same trip. Canonical before/after request comparison found only `budget` changed. Destination research, flights and activities were JSON-identical; hotels and itinerary changed. | Pass |
| Desktop | Browser viewport approximately 1304 pixels; inspected brief and itinerary, readable layout, reachable navigation and revision controls. | Pass |
| Mobile | 390 × 844 viewport: clarification, restored itinerary and Options inspected. Document widths 390 (clarification) and 375 (scrolling itinerary/options), no horizontal page overflow. Navigation and revision controls usable. | Pass |
| Missing-trip recovery | All-zero UUID route displayed “Trip not found” with “Start a new trip”; link returned to the landing page. | Pass |
| Planning failure safety | Existing controlled backend regressions cover failed workflow/replan, timeout, capacity and persistence errors, preservation and same-message retry. Frontend regressions cover error mapping, preserved correction and retry UI. These are test doubles, not a live injected outage. | Pass, controlled evidence |
| HTTPS/hardening | Live `/health` returned 200 with `{"status":"healthy"}`, no-store, HSTS, CSP, no-referrer, nosniff, frame denial and disabled camera/location/microphone. `/docs` returned 404. | Pass |
| Browser origin boundary | Live OPTIONS from the frontend origin returned 200 with exact allow-origin. `https://example.com` returned 400, without allow-origin. | Pass |

Synthetic test trip identifiers and raw saved state remain local; this report
omits durable trip access links. Browser screenshots were inspected during QA;
this PR does not include new screenshot files. P3 owns the portfolio image package.

## Validation and limits

- Existing backend suite: 115 passed. Includes API, replanning and hardening.
- Existing frontend suite: 26 passed. Audit-policy suite: five passed.
- Frontend lint and production build passed (Next.js 16.3.8).
- Reviewed frontend audit: zero blocking high/critical findings; the existing
  dev-only braces advisory exception remains and expires November 8, 2026.
- Backend container build passed; runtime UID 10001 and local `/health` smoke passed. The temporary QA container was stopped.
- Pinned backend lockfile audit: no known vulnerabilities. The normal Windows audit could not install Linux-only uvloop; `--disable-pip --no-deps` audited the fully pinned lock entries directly. Linux CI runs the normal resolving audit. No tests, prompts, application code or model configuration changed. Live Gemini
  and Tavily calls occurred through the normal browser workflow, separately from
  the synthetic replay baseline. No new inference evaluation was required.

This is a browser smoke/acceptance check, not exhaustive accessibility, physical
mobile-device, load, or real-world travel-feasibility certification. One route and
one budget correction do not establish general model accuracy or provider uptime.
No live model outage was injected; failure safety uses controlled regression evidence.

Flight prices were absent and the UI said “Price not found.” Some hotel prices
were absent too; displayed rates remain research candidates. Activity costs used
EUR while the trip budget used USD. No complete comparable-currency trip total,
confirmed availability, opening hours or transit-feasibility guarantee was verified.
Source links rendered; their current contents and every generated factual claim
were not independently audited. These remain the documented portfolio boundaries.

## Outcome and next milestone

No blocking functional issue was observed in the exercised portfolio flow.
P2's functional acceptance is complete; merge its evidence PR after CI passes.
Next is P3: package the engineering story, fresh portfolio screenshots and honest
limitations. Voice, timeline, MCP, booking and multilingual feature work remain deferred.

