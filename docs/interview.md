# Tripzy: interview walkthrough

## A 60-second introduction

“I built and shipped Tripzy as a portfolio project with AI-assisted development. A traveler describes a trip in natural language, and Tripzy turns that into a durable workspace with candidate research and a daily itinerary.

The core design is probabilistic interpretation with deterministic application truth. Gemini interprets intent and supports bounded reasoning, but Python owns canonical state, workflow decisions, validation and persistence.

A budget-only correction is a concrete example. Python invalidates hotels and itinerary, while keeping unrelated destination, flight and activity research. Processing works on a copy, and the API saves only after success, so a failed operation leaves the previous saved trip available.

I verified the live workflow and measured model behavior rather than presenting it as universally accurate. Extraction can still introduce unintended fields, and the project does not establish bookable availability or complete budget feasibility.”

## Five-minute demonstration

| Time | Show or explain | Evidence |
| --- | --- | --- |
| 0:00–0:45 | Define the persistent planning problem and show the product. | [89-second recording](https://github.com/user-attachments/assets/badc1551-7f3c-4a09-825c-d4b3ef807f50) |
| 0:45–1:45 | Follow UI → API → interpretation/research → deterministic state/validation → save. | [Architecture](portfolio-story.md#decisions-that-can-be-inspected-in-code) |
| 1:45–2:45 | Explain refresh restoration, then a budget-only revision and its dependency graph. | [Replanning](../app/services/replanning.py), [live acceptance](p2-demo-acceptance.md) |
| 2:45–3:45 | Discuss the empty-interest regression and failure-safe persistence. | [Replanning tests](../tests/test_replanning.py), [API tests](../tests/test_api.py) |
| 3:45–5:00 | Separate controlled regressions, extraction measurements and actual travel truth; explain the stopping point. | [Evaluations](evals.md), [limits](portfolio-story.md#honest-limitations-and-tradeoffs) |

The recording is the reliable demonstration artifact; a live run can take minutes or hit provider quotas. Use synthetic details if demonstrating live. Do not deliberately fail or overload production to prove recovery.

## Questions to prepare for

**What makes this agentic?** Specialist workflows interpret requirements, perform bounded research through tools and synthesize structured artifacts under an application-controlled workflow. It is not an unrestricted autonomous booking agent. The itinerary stage consumes existing structured research rather than issuing new searches.

**Why not let the model own everything?** Intent interpretation varies. Explicit Python state and dependency rules make transitions inspectable and testable. Deterministic checks constrain dates, day counts and eligible activities; they do not determine every real-world travel fact or guarantee the extraction matches the user's intent.

**What was a concrete bug?** A budget-only correction could emit `interests_replace: []` and erase existing interests. Empty replacement is now treated as omitted; non-empty replacement and add/remove operations remain explicit. Explain the regression test rather than claiming all unintended edits are solved.

**How does failure safety work?** Processing operates on a copy and persists only after the complete operation succeeds. Failures, timeouts and overload do not overwrite the previously saved state. That does not provide per-trip locking: concurrent revisions can still race.

**How did you evaluate it?** Separate 115 backend regressions, 26 frontend tests and five audit-policy tests from a fixed 60-case portfolio subset run three times against Gemini with synthetic search replay. Intake exact trial pass averaged 63.3%; correction exact pass was 90.0%; tested itinerary invariants passed all 30 trials. The 3.89% unrequested-field fraction exceeded the old 2% target. Full budget adherence was unmeasured. One provider execution failure was recovered on resume and retained in history.

**Why did the video show no flights?** That run returned no supported flight options, and the empty state was kept. P2's earlier run returned three candidates. Results vary with providers and searches; neither run establishes bookable availability.

**What protects the public demo?** Server-only credentials, exact-origin CORS, body/message limits, redacted errors, process-local rate/capacity controls and a non-root backend. Trip URLs function as access links; there are no account-level API authorization checks. Database RLS is not a substitute for API authorization. The existing dev-only audit exception expires November 8, 2026.

**What would you improve next?** For a larger product: extraction quality, comparable costs and feasibility evidence, account authorization and per-trip concurrency controls. Voice, a visible timeline and MCP remain deferred. The portfolio stopping point is a shipped, bounded workflow with evidence, not a new feature checklist.

**How did you use AI?** ChatGPT and Codex assisted development. Explain your product scope, chosen boundaries, inspected implementation and validation. Be ready to trace the code paths and reproduce the regression instead of claiming unaided authorship.

## Code paths to rehearse

Read [TripManager](../app/services/trip_manager.py), [replanning](../app/services/replanning.py), [conversation orchestration](../app/services/conversation.py), [itinerary validation](../app/services/itinerary_planning.py), [API persistence boundary](../app/api.py) and [CI](../.github/workflows/ci.yml). Explain where model output stops and application-owned state begins.
