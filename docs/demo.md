# Tripzy portfolio demo

Use this as a short, repeatable walkthrough for a portfolio review or interview.

## 1. Frame the system

Tripzy is not a free-form chatbot. The LLM interprets natural language and performs bounded reasoning, while deterministic Python owns state, workflow, validation, persistence, and dependency invalidation.

## 2. Create a complete trip

Open the live frontend and use a complete mission, for example:

> Plan 5 days from Karachi to Istanbul in September 2027 for two travelers, around $2,000. History and food, not rushed.

Show that Tripzy creates one durable trip workspace and turns the mission into structured state plus research-backed artifacts.

## 3. Show persistence

Copy the trip URL, refresh it, and reopen it directly. The same trip should restore from the backend persistence layer.

## 4. Show selective replanning

Submit a narrow correction:

> Change the budget to $2,500.

Explain that the correction is interpreted into structured fields, Python computes which artifacts depend on those changed fields, and unrelated requirements such as interests remain unchanged.

## 5. Explain failure safety

Tripzy persists a revised plan only after successful processing. If planning fails, the previous durable state remains available and the same correction can be retried safely.

Do not intentionally break the public production service for a portfolio demo. Use automated regression evidence or a controlled development environment to demonstrate the failure path.

## 6. Close with the engineering boundary

The core design choice is simple:

> probabilistic interpretation; deterministic application truth.

Useful evidence in the repository:

- `app/services/replanning.py` — dependency-driven selective replanning
- `app/services/conversation.py` — workflow orchestration
- `app/services/trip_repository.py` — persistence boundary
- `tests/test_replanning.py` — correction/failure regression coverage
- `.github/workflows/ci.yml` — reproducible release gate
- `docs/database.md` — database bootstrap and RLS contract
- `docs/deployment.md` — production deployment contract
