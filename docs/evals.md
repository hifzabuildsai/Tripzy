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
grader, fixture or Python/provider-library version is rejected. Checkpoints are local run artifacts,
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

Evaluation reports record the actual Python and provider-library versions.
Local measurements may differ from the locked Linux production runtime; the
baseline documents that environment rather than claiming production parity.
Per-trial duration currently includes queue wait and is not a standalone
inference-latency benchmark.

Completed trial execution rates describe the final retained measurements.
`execution_history` separately retains terminal failures from earlier run
invocations, including trials recovered on resume. It is not a count of every
HTTP retry inside the SDK. A resumed baseline must not be described as perfect
provider availability.

## Recorded v1.0.0 portfolio baseline

[JSON evidence](../evals/baselines/v1.0.0.json) ·
[Markdown report](../evals/baselines/v1.0.0.md)

60 cases × 3 repeats = 180 completed trials against Gemini, with synthetic
research replay. One provider `InternalServerError` caused an invalid first
report; only that trial was resumed. All measured quality failures were
retained. The final baseline has no unresolved execution failures and retains
that earlier failure in `execution_history`.

| Suite | Cases | Mean exact trial pass | Worst repeat |
|---|---:|---:|---:|
| Intake extraction | 20 | 63.3% | 60.0% |
| Correction extraction | 30 | 90.0% | 90.0% |
| Itinerary invariants | 10 | 100.0% | 100.0% |

Intake mean field precision: 85.8%; recall: 78.5%. Correction interest-operation
correctness: 100%; mean unrequested-field fraction: 3.89%, above the old v1.1
plan's 2% target. The portfolio baseline documents this remaining limitation;
it does not claim that target was met. Budget adherence is unmeasured in all
30 itinerary trials because comparable item costs were absent.

Every budget-only regression repeat passed. Common measured failures include
local-script place names instead of canonical English names, partial dates
being made too specific, and missing serialized default-USD evidence. The
JSON includes per-language results and expected/actual failure examples.

Measured environment: Python 3.14.6, openai 3.3.1, openai-agents 0.22.0,
pydantic 2.13.4 and tavily-python 0.7.27. Production/CI use Python 3.12 and the
locked dependencies. These are local boundary measurements, not an assertion
of an identical deployed runtime or verified real-world travel quality.
