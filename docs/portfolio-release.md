# Tripzy v1.0.1: accepted portfolio checkpoint

Release date: October 8, 2026. Tag: `v1.0.1`. Accepted source commit: `62266364c2dbd34f0edac75003176cea7c43bcb1`, the merged P4 PR. The existing `v1.0.0` tag remains unchanged.

This tag identifies the accepted repository checkpoint containing P1–P4. P5's resume/interview documents are delivered in a separate reviewable PR after that checkpoint. It does not claim a new feature release, that all deployment revisions equal the tag, or completion of the deferred v1.1 roadmap. The model baseline retains its original `v1.0.0` filename and provenance.

## Evidence index

| Milestone | Delivered evidence |
| --- | --- |
| P1 | [Fixed repeated model baseline](evals.md), [JSON](../evals/baselines/v1.0.0.json), [PR #12](https://github.com/hifzabuildsai/Tripzy/pull/12) |
| P2 | [Live acceptance record](p2-demo-acceptance.md), [PR #13](https://github.com/hifzabuildsai/Tripzy/pull/13) |
| P3 | [Engineering case study](portfolio-story.md), [capture notes](images/README.md), [PR #14](https://github.com/hifzabuildsai/Tripzy/pull/14) |
| P4 | [89-second recording](https://github.com/user-attachments/assets/badc1551-7f3c-4a09-825c-d4b3ef807f50), [verification](p4-demo.md), [PR #15](https://github.com/hifzabuildsai/Tripzy/pull/15) |
| P5 | [Copy-ready resume wording](resume.md), [interview walkthrough](interview.md), this release record |

The [accepted commit's release gate](https://github.com/hifzabuildsai/Tripzy/actions/runs/37732194048/job/113163615550) passed. It runs regression tests, dependency audits, Gitleaks, frontend lint/build, Docker build, non-root checks and a container health smoke test. The gate validates code; it never deploys it. `/health` is process health, not provider/database readiness.

## What changed since v1.0.0

The portfolio work adds measured evaluations, live acceptance evidence, patched frontend dependencies with a reviewed dev-only advisory exception, architecture/limitations documentation, screenshots and a recorded demo. It does not add voice, timeline, MCP, accounts or bookings.

The baseline contains 180 completed trials across 60 fixed cases. Intake exact trial pass averaged 63.3%; correction exact pass was 90.0%; the unrequested-field fraction was 3.89%. Tested itinerary invariants passed 30 trials, while full budget adherence was unmeasured. Measurements used local Python/provider-library versions that differ from the locked production/CI runtime. One recovered provider failure remains recorded in execution history.

The public frontend and API are available, and the P2/P4 records describe the flows actually checked. Those records do not establish an exhaustive production audit, guaranteed availability, live price accuracy or complete itinerary feasibility. P4 visibly retains an empty flight-results state.

## Maintenance and stopping point

The dev-only frontend advisory exception expires November 8, 2026 and then fails closed. Review the upstream fix or explicitly re-evaluate the policy before that date; raw npm audit still reports the acknowledged advisory. Provider quotas, credentials and hosting require ongoing care if the public demo remains available. There is no automatic monitoring implied by this release record.

After P5 is accepted, the approved portfolio milestone sequence is finished. Use the live demo, video, source and interview package for applications. Any further implementation should start with a new explicit scope; the deferred v1.1 feature plan does not resume automatically.
