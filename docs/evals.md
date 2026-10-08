# Tripzy portfolio evaluations

## What is measured

Tripzy is a portfolio project. These evals measure the existing v1.0.0 model
boundary without changing prompts, extraction tools, or the inference model:

- intake field precision/recall and unrequested fields at the serialized extraction boundary;
- correction exact match, unrequested fields and interest operations;
- structured itinerary invariants with fixed synthetic research.

They do **not** establish live search quality, real-world availability, opening
hours, transit feasibility, or a complete trip budget. The itinerary suite grades
structured model output before the production invariant validator rejects it,
so invalid dates/activities become measured quality failures.

A known interpretation limit: `extract_trip_request` serializes with
`exclude_defaults=True`, so USD can be omitted from tool output even when the
application retains its default USD currency. The intake grader records this
as missing extraction evidence; it does not imply the saved trip lost USD.
Multilingual canonical-name mismatches are measured limitations, not promises
that the product currently supports every tested language.

## Profiles

The full datasets contain 40 intake, 60 correction and 10 itinerary cases.
`--profile full` remains the default CLI profile.

The portfolio baseline uses a fixed subset of 20 intake, 30 correction and all
10 itinerary cases, repeated three times (180 trials). Intake/correction are
60% English and 40% multilingual, retaining every dataset language and the
budget-only interests regression. Selection uses dataset order and round-robin
language sampling before any model result is inspected. The report records
exact case IDs, language counts and a source/fixture fingerprint.

This narrower baseline supersedes the full-dataset baseline requirement in the
original M19.1 plan for the approved portfolio scope. It is not a claim about
all possible trips or languages. Full-suite runs remain available.

## Run

Install locked dependencies and configure `GEMINI_API_KEY` server-side.
Search replay uses committed fixtures and makes no Tavily requests. Gemini
inference still calls the network, costs quota, and is nondeterministic.

```bash
python -m evals.run --suite all --profile portfolio --search-mode replay --repeat 3 --concurrency 1 --request-interval 9 --checkpoint evals/reports/portfolio-checkpoint.json --output evals/reports/v1.0.0-portfolio
```

Repeat the identical command to resume completed trials after an interruption
or quota reset. Completed quality failures are retained too; resume does not
cherry-pick successful outputs. Provider/execution failures are retried.
A checkpoint from a different model, dataset, repeat count, application,
grader or fixture version is rejected. Checkpoints are local run artifacts,
not committed baselines.

Transient rate limits respect the provider retry delay (bounded to 60 seconds).
A daily-quota error stops new calls. Reports are written, but any execution
failure makes the run exit unsuccessfully and the baseline invalid.
Normal pushes never trigger inference. Both GitHub eval workflows are manual
and separate from the release gate; they upload reports/checkpoints, never
commit results automatically.

## Read results honestly

- Trial pass rate includes execution failures as unsuccessful trials.
- Quality metrics exclude unavailable measurements and report measured counts.
- Execution success is reported separately; zero usable outputs cannot become
  a perfect unrequested-field score.
- Budget grading covers only exposed itinerary item costs in the request's
  currency. No costs, negative costs or mixed/unknown currencies are unmeasured
  (`null`), not a budget success. Flights, hotels and meals may be absent.
- Per-case failures remain in JSON and Markdown, including multilingual cases.
- A valid baseline may have poor quality scores: a baseline measures existing
  behavior; this milestone does not tune prompts to make the scores prettier.

## Portfolio ship checklist

1. P1: finish existing eval PR, valid repeated baseline, green release gate.
2. P2: verify deployed revisions and the core demo acceptance matrix.
3. P3: package architecture, evidence, screenshots and limitations.
4. P4: record a 60–90-second demonstration.
5. P5: accepted release tag, resume bullets and interview walkthrough.

Multilingual features, voice, live timeline, MCP, bookings and advanced travel
feasibility are deferred. The approved portfolio scope takes precedence over
the broader v1.1 feature roadmap.

## Release-gate dependency maintenance

October 8 validation found new frontend security advisories. Next.js and its
ESLint config are patched to 16.3.8; compatible sharp/source-map-js fixes are
resolved in the lockfile. Application UI and planning behavior are unchanged.

`npm run audit` still rejects every high/critical finding except the exact
unpatched advisory [GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm)
and its dependency chain when **every affected node is dev-only** in the
lockfile. In this repo braces is reached through eslint-config-next/fast-glob,
not runtime dependencies; lint scans repository-owned paths, not user-supplied
patterns. The exception expires November 8, 2026, then fails closed. New
advisories, runtime occurrences and malformed reports fail the gate. Tests
cover those conditions. Raw `npm audit` still reports the acknowledged issue;
this project does not claim zero advisories.

Use `npm run audit:test && npm run audit` for the reviewed project audit.
