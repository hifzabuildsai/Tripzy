# P4: recorded portfolio demonstration

Recorded against the public Tripzy frontend and API on October 8, 2026, using synthetic travel details. Source checkout: `8218554a0c89d4cceda97b580fa7237ead3b0863` (P3 merged). This milestone changes documentation only.

## What the demonstration shows

1. A complete mission: Karachi to Istanbul, September 10, 2027, five days, two travelers, $2,000 USD, history and food, relaxed pace.
2. The trip brief, destination research, flight/hotel candidates and itinerary.
3. A browser refresh restoring the saved workspace.
4. A narrow correction: change only the total budget to $2,500 USD.
5. The revised brief and five-day itinerary.

Before/after canonical API state was inspected for the same synthetic trip. Only the request's `budget` field changed. Destination research, flight options and activity options remained identical; the final state was `itinerary_planned` with five days. This is evidence for this observed run, not a universal model guarantee. The repeated [evaluation baseline](evals.md) records extraction failures and unmeasured full-budget adherence.

## Editing and privacy

The silent, captioned edit targets 89 seconds. It preserves one continuous source sequence, trims setup/closing idle time and speeds up the two provider waits with explicit captions. It does not represent those waits as real-time latency. Browser chrome and the trip access URL are masked throughout, including the cover. No synthetic pointer events were added. Raw footage, full trip snapshots and the controller journal remain outside Git.

Research outputs remain candidates: the demonstration does not establish bookable availability or complete travel-budget feasibility. Failure-safe persistence is covered by regression tests; this recording does not intentionally cause a production failure.

## Validation

- Live plan, refresh restoration and budget-only revision completed successfully.
- 115 backend tests passed; fully pinned dependency audit found no known vulnerabilities.
- 26 frontend tests and five audit-policy tests passed; lint and production build passed.
- The reviewed frontend audit passed with the existing dev-only advisory exception documented in [evals](evals.md); raw npm audit is not clean.
- Docker release image built successfully after starting the local Docker daemon.
- No prompts or extraction tools changed, so no new paid model evaluation was run.

Final media playback, attachment and CI verification are recorded in the milestone PR.
