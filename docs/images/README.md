# Product screenshots

The root README uses fresh production captures from October 8, 2026:

| File | View | Viewport |
| --- | --- | --- |
| [tripzy-p3-landing.jpg](tripzy-p3-landing.jpg) | Landing page | 1440 × 1000 |
| [tripzy-p3-discover.jpg](tripzy-p3-discover.jpg) | Istanbul destination research | 1440 × 1000 |
| [tripzy-p3-itinerary.jpg](tripzy-p3-itinerary.jpg) | Five-day Istanbul itinerary | 1440 × 1000 |
| [tripzy-p3-mobile.jpg](tripzy-p3-mobile.jpg) | Same itinerary, mobile viewport | 390 × 844 |

Source: https://tripzy-liard.vercel.app. Desktop Chrome/Playwright captures and
mobile viewport emulation, device scale factor 1, JPEG quality 85. Captures waited
for the existing entrance animations. This is viewport emulation, not evidence
of a physical phone test. No application styling, DOM content or image pixels
were edited to stage the result.

The saved trip is the synthetic P2 QA example: Karachi → Istanbul, September
10-14, 2027, two travelers, history/food, relaxed pace. P2 revised its budget
from USD 2,000 to USD 2,500. Captures read the existing durable state; they did
not submit another mission or correction, invoke planning, or change production
configuration. Full trip access URLs are deliberately omitted.

These show the deployed planning UI, not verified prices, availability, transit
feasibility or confirmed bookings. The [P2 acceptance record](../p2-demo-acceptance.md)
and [portfolio case study](../portfolio-story.md) explain those boundaries.
No browser chrome, personal account details or credentials appear in the images.

Earlier release captures (`tripzy-landing.png`, `tripzy-landing.webp`,
`tripzy-discover.webp`, `tripzy-itinerary.webp`) remain available but are no
longer the root README previews. Their precise capture timestamps were not
recorded here. `tripzy-system-architecture.png` is a diagram, not a production
screenshot.

## System architecture diagram

Updated October 9, 2026, against merged main at cece9b10a2db82d471f4c055ddbb883482a44d31. The built-in image generator edited the existing diagram; its text and provider connections were reviewed against ConversationService, TripManager, replanning.py and the API save boundary. It removes the former booking claim and shows research candidates, selective budget replanning, deterministic validation and save-after-success persistence. Logical responsibilities are simplified; clarification paths are described in the README, and dashed provider links do not imply parallel execution. [Generation prompts](tripzy-system-architecture.prompt.md).

## Focused documentation explainers

Authored as editable SVGs on October 9, 2026, against main `c74819ab3117ea69743fd14df9080683ceb4a2cf`. These explain the existing system; no application, database or production configuration changed. Each SVG has embedded title/description text, and the consuming document has an alt description and scope caption. Diagrams summarize the main idea; exact commands, source contracts and complete evidence remain in the documents.

| SVG | Consuming document | Verified source |
| --- | --- | --- |
| [Revision and failure safety](tripzy-revision-failure-safety.svg) | [Case study](../portfolio-story.md) | `replanning.py`, `session_registry.py`, `api.py`, itinerary validation |
| [Deployment boundaries](tripzy-deployment-boundaries.svg) | [Deployment](../deployment.md) | Deployment contract, hardening and CI workflow |
| [Evaluation pipeline](tripzy-evaluation-pipeline.svg) | [Evaluations](../evals.md) | Eval runner, fixed portfolio profile and retained baseline |
| [Database access](tripzy-database-access.svg) | [Database](../database.md) | Both SQL migrations, `TripState` and repository adapters |

Local PNG previews were rendered and visually reviewed for text clipping, arrow placement and reading order. SVG XML and local document/image links were checked. The files contain no embedded scripts, external image/font dependencies, real trip identifiers or credential values. The evaluation diagram reuses measured evidence; no provider calls or new inference run were made to produce it.
