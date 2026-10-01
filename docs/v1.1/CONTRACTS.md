# Tripzy v1.1 — Contracts

These contracts are locked by M19.0 before implementation begins.

They define the interfaces M19.1–M19.4 must implement without weakening
Tripzy's existing deterministic application boundaries.

## 1. Eval contracts

### Common JSONL case envelope

Eval datasets are JSONL. Each line is one case.

Common fields:

- `id: str` — stable unique case identifier.
- `suite: str` — suite name.
- `language: str` — BCP-47 input-language label.
- `input: object` — suite-specific input.
- `expected: object` — suite-specific expected result.
- `tags: list[str]` — optional grouping or regression tags.

Expected application values remain canonical even when the input is
multilingual.

### `intake_extraction`

Input:

- `messages: list[str]`
- optional `current_request: object`

Expected:

- `fields: object`

`fields` is a subset of the current `TripRequest` fields:

- `origin`
- `destination`
- `start_date`
- `end_date`
- `start_date_text`
- `end_date_text`
- `duration_days`
- `travelers`
- `budget`
- `currency`
- `interests`
- `travel_style`

The grader reports field precision, field recall, and unrequested-field rate.

### `correction_extraction`

Input:

- `current_request: object`
- `message: str`

Expected:

- `correction: object`

`correction` uses the current `TripCorrection` fields:

- `origin`
- `destination`
- `start_date`
- `end_date`
- `start_date_text`
- `end_date_text`
- `duration_days`
- `travelers`
- `budget`
- `currency`
- `travel_style`
- `interests_add`
- `interests_remove`
- `interests_replace`

The grader reports exact match, unrequested-field rate, and interest-operation
correctness.

An empty `interests_replace: []` with no explicit interest change is treated
as not provided, matching the current `apply_correction()` behavior.

### `itinerary_invariants`

Input:

- `trip_request: object`
- replay-fixture-backed research required by the runner

Expected assertions:

- itinerary day count equals `duration_days`
- dates are contiguous from `start_date`
- itinerary destination and traveler count match application truth
- each scheduled named visitor activity maps exactly to an existing
  `activity_options` candidate
- researched flight and hotel candidates remain candidates, never selected or
  booked truth
- budget assertions are applied only where exposed structured costs support
  them

These mirror the current checks in `ItineraryPlannerService` and the existing
candidate-only research boundary.

### Eval report schema

The JSON report is versioned:

- `schema_version: 1`
- `generated_at: str`
- `model: str`
- `search_mode: "live" | "record" | "replay"`
- `repeat: int`
- `suites: object`
- `overall: object`

Each suite report contains:

- `case_count: int`
- `repeat_count: int`
- `metrics: object`
- `mean: object`
- `min: object`
- `failures: list[object]`

Each failure contains:

- `case_id: str`
- `repeat: int`
- `metric: str`
- `expected: object | scalar | list`
- `actual: object | scalar | list`

The runner also writes a Markdown summary containing the same aggregate scores
and per-case failures.

The current inference model is `gemini-3.5-flash-lite` unless
`GEMINI_MODEL` explicitly overrides it.

Eval reports must never contain API keys or other secret values.

---

## 2. Language contract

### State ownership

Add:

`TripState.response_language: str = "en"`

`response_language` is conversation/application state. It is not part of
`TripRequest`.

A language change therefore:

- must never appear in `changed_fields`
- must never invalidate `destination_research`
- must never invalidate `flight_options`
- must never invalidate `hotel_options`
- must never invalidate `activity_options`
- must never invalidate `itinerary`

### Detection

The existing extraction tools gain:

`user_language: str | None`

This applies to both:

- `extract_trip_request`
- `extract_trip_correction`

The value is a BCP-47 language tag.

Python updates `TripState.response_language` on each turn only when the
returned language value is valid.

Missing or invalid language output preserves the previous
`response_language`.

English input must not require an additional language-detection LLM call.

### Canonical application state

Language affects presentation, not Tripzy's canonical trip truth.

Regardless of input language:

- place names are stored as standard English names
- interests are stored as lowercase English canonical keys
- resolved dates use the existing ISO `YYYY-MM-DD` semantics
- unresolved calendar expressions continue through the existing deterministic
  partial-date path
- Tavily research queries remain English

### Localization

Service contract:

`localize(text: str, lang: str) -> str`

Rules:

- `lang == "en"` returns the source text unchanged with no LLM call
- localization translates only and adds no facts
- Western digits are preserved
- amounts and currency codes are preserved
- ISO dates are preserved
- URLs are preserved
- IATA codes are preserved

Before accepting localized output, deterministic Python extracts protected
tokens from the English source and verifies that every protected token remains
present in the localized output.

Localization has an approximately 20-second timeout inside the existing
240-second planning budget.

On timeout, invalid output, or guard failure:

- return the English source
- emit the redacted log event `localization_fallback`
- do not log the full prompt or secret values
- do not mutate trip truth or artifact invalidation

User-facing text covered by this layer includes:

- `TripManager.get_next_question()`
- combined planning responses
- revision acknowledgements
- user-facing planning errors

Stored research remains canonical and is not translated by this contract.

---

## 3. `POST /transcribe` API

### Purpose

Convert one short push-to-talk recording into reviewable text.

Transcription does not create a trip, send a trip message, or persist audio.

The returned transcript is inserted into the existing composer and never
auto-submitted.

### Request

`POST /transcribe`

Content type:

`multipart/form-data`

Multipart field:

`audio`

Accepted audio media types:

- `audio/webm`
- `audio/ogg`
- `audio/mp4`
- `audio/mpeg`
- `audio/wav`

Client recording duration is capped at 45 seconds.

The route has its own approximately 1.5 MiB request-body limit. This exception
is scoped only to `POST /transcribe`; it must not loosen the existing 16 KiB
JSON request-body limit used by Tripzy's current write endpoints.

### Rate limit

`POST /transcribe` has an explicit per-client limit of 10 requests per
60 seconds.

This limiter is process-local under Tripzy's current single-Railway-replica
deployment assumption.

### Response

HTTP 200:

```json
{
  "text": "string",
  "language": "BCP-47 language tag"
}
```

### Errors

- `413` — request exceeds the route-specific size limit
- `415` — unsupported audio media type
- `422` — malformed multipart request or missing/empty `audio`
- `429` — transcription rate limit exceeded
- `503` — transcription provider temporarily unavailable

Raw audio bytes are never written to disk, persisted in `TripState` or
Supabase, or written to application logs.

Transcription uses Gemini audio input. M19.3 must first verify whether Tripzy's
existing Gemini OpenAI-compatible endpoint supports the required audio input.
If it does not, only this transcription call may use the native Gemini SDK.

The existing production `Permissions-Policy` currently disables microphone
access at the API layer. If a frontend policy is introduced for browser
recording, it must allow `microphone=(self)` without weakening unrelated
camera or geolocation restrictions.

---

## 4. Run-event schema v1

Run events are application-owned Pydantic data.

Every event contains:

- `v: Literal[1]`
- `type: str`

The SSE event identifier is transport metadata and is not application truth.

### Stage names

The run timeline maps onto Tripzy's existing planning stages:

- `destination`
- `flights`
- `hotels`
- `activities`
- `itinerary`

These correspond to the current status sequence
`researching_destination` / `destination_researched`,
`researching_flights` / `flights_researched`,
`researching_hotels` / `hotels_researched`,
`researching_activities` / `activities_researched`, and
`planning_itinerary` / `itinerary_planned`.

### Event types

#### `run_started`

No additional payload.

#### `stage_started`

- `stage: str`

#### `tool_call`

- `tool: str`
- `query: str`

#### `source_found`

- `stage: str`
- `title: str`
- `url: str`

#### `artifact_ready`

- `kind: str`
- `count: int`
- `preview: list[object]`

#### `replan_plan`

- `changed_fields: list[str]`
- `rerun: list[str]`
- `kept: list[str]`

`changed_fields` is derived from the existing correction comparison rules,
and `rerun` / `kept` are derived from the existing artifact dependency
graph.

#### `stage_completed`

- `stage: str`
- `duration_ms: int`

#### `message`

- `text: str`

The text follows the language contract.

#### `run_completed`

No additional payload.

#### `run_failed`

- `reason: str`
- `preserved_previous: Literal[true]`

No event payload contains API keys, secret values, or trip IDs.

### Run creation

`POST /trips/{trip_id}/runs`

Request:

```json
{
  "message": "string"
}
```

`message` uses the existing `TripMessageRequest` limit: 1–4,000
characters.

The existing public write rate limit applies.

The existing planning limits remain:

- maximum concurrent planning jobs: 2
- queue timeout: 1 second
- planning timeout: 240 seconds

Overload returns `503` before a run is accepted.

Accepted response:

HTTP 202

```json
{
  "run_id": "string"
}
```

### SSE

`GET /trips/{trip_id}/runs/{run_id}/events`

Each application event is framed as:

```text
id: <monotonic event id>
event: <event type>
data: <JSON event payload>
```

Event IDs are ordered within a run.

The server emits an SSE heartbeat comment approximately every 15 seconds while
the stream remains open.

The stream closes after `run_completed` or `run_failed`.

### Reconnect

Clients reconnect with:

`Last-Event-ID: <last received id>`

The server replays events strictly after that ID and then resumes live
delivery.

`GET /trips/{trip_id}` exposes `active_run_id` while a run is active so a
page refresh can reattach.

Run state is process-local and assumes one Railway backend replica.

Completed run state is eligible for cleanup approximately 15 minutes after the
terminal event.

### Persistence invariant

Run events do not become the source of `TripState` truth.

The background planning task works against reconstructed/working state and the
repository is updated only after successful completion.

`run_failed`, timeout, and overload must leave the previously persisted plan
unchanged.

The existing `POST /trips/{trip_id}/messages` endpoint remains available for
backward compatibility.
