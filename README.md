# Tripzy

Tripzy is an agentic AI travel planning application that turns conversational trip requirements into structured destination research, travel options, activities, and a day-by-day itinerary.

The system is built around a deliberate architecture:

> LLMs handle interpretation and reasoning.  
> Deterministic application code owns state, workflow, validation, and invariants.

Tripzy is currently a backend-first project built with Python, FastAPI, the OpenAI Agents SDK, Gemini, Tavily, and Supabase PostgreSQL.

## What Tripzy Does

A traveler can progressively provide information such as:

- origin
- destination
- travel dates
- trip duration
- number of travelers
- budget
- interests
- travel style

Tripzy collects missing requirements conversationally and then runs specialized planning stages for:

1. Destination research
2. Flight research
3. Hotel research
4. Activity research
5. Structured itinerary planning

The resulting trip state is persisted in PostgreSQL and can be accessed through the FastAPI backend.

## Architecture

```text
Client / Frontend
       |
       v
    FastAPI
       |
       v
ConversationService
       |
       v
   TripManager
       |
       +-----------------------------+
       |                             |
       v                             v
Requirement Collection       Research Workflows
                                     |
                    +----------------+----------------+
                    |                |                |
                    v                v                v
              Destination         Flights          Hotels
                 Research
                                                     |
                                                     v
                                                 Activities
                                                     |
                                                     v
                                           Itinerary Planner
                                                     |
                                                     v
                                               TripState
                                                     |
                                                     v
                                              TripRepository
                                                     |
                                                     v
                                          Supabase PostgreSQL
```

## Core Design Principles

### Application state belongs to Python

The language model does not own Tripzy's application state.

Structured Python models and services control:

- trip requirements
- workflow progression
- status transitions
- date semantics
- persisted state
- itinerary validation

### Research and planning are separate

Research agents gather candidate travel information.

The itinerary planner consumes the structured research already owned by the application rather than performing new web searches.

This prevents the planning stage from silently becoming another research agent.

### Research is not booking

Flight, hotel, and activity results are research candidates.

Tripzy does not claim that:

- a flight has been booked
- a hotel has been selected
- a ticket is available
- a displayed price is guaranteed
- live availability has been confirmed

### Deterministic invariants stay deterministic

Important rules such as itinerary dates and trip duration are enforced by application code rather than delegated entirely to the LLM.

For the current MVP:

```text
duration_days = number of calendar trip days
```

For example:

```text
start_date:    2027-09-10
duration_days: 5

trip dates:
2027-09-10
2027-09-11
2027-09-12
2027-09-13
2027-09-14
```

## Technology Stack

### Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

### Agentic AI

- OpenAI Agents SDK
- Gemini through Google's OpenAI-compatible endpoint

### Travel Research

- Tavily

### Persistence

- Supabase
- PostgreSQL
- JSONB trip state
- Row Level Security enabled

### Testing

- pytest
- FastAPI TestClient
- deterministic in-memory repository test double

## Project Structure

```text
tripzy/
├── app/
│   ├── agents/
│   │   ├── trip_planner.py
│   │   ├── destination_researcher.py
│   │   ├── flight_researcher.py
│   │   ├── hotel_researcher.py
│   │   ├── activity_researcher.py
│   │   └── itinerary_planner.py
│   │
│   ├── models/
│   │   ├── api.py
│   │   ├── trip.py
│   │   ├── state.py
│   │   ├── research.py
│   │   ├── flight.py
│   │   ├── hotel.py
│   │   ├── activity.py
│   │   └── itinerary.py
│   │
│   ├── services/
│   │   ├── trip_manager.py
│   │   ├── conversation.py
│   │   ├── research.py
│   │   ├── flight_research.py
│   │   ├── hotel_research.py
│   │   ├── activity_research.py
│   │   ├── itinerary_planning.py
│   │   ├── session_registry.py
│   │   ├── trip_repository.py
│   │   ├── in_memory_trip_repository.py
│   │   └── supabase_trip_repository.py
│   │
│   ├── tools/
│   │   ├── travel_search.py
│   │   ├── trip_extraction.py
│   │   ├── flight_search.py
│   │   ├── hotel_search.py
│   │   └── activity_search.py
│   │
│   ├── api.py
│   ├── config.py
│   └── main.py
│
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/hifzabuildsai/Tripzy.git
cd Tripzy
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Tripzy

```powershell
python -m pip install -e ".[dev]"
```

### 4. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then provide your own credentials.

Example configuration:

```env
APP_ENV=development
DEBUG=true

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite

TAVILY_API_KEY=your_tavily_api_key

SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_supabase_secret_key

CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Never commit `.env` or backend secret keys.

## Run the CLI

```powershell
python -m app.main
```

## Run the API

```powershell
uvicorn app.api:app --reload
```

The local API will normally be available at:

```text
http://127.0.0.1:8000
```

Interactive FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### Health

```http
GET /health
```

### Create a trip

```http
POST /trips
```

Creates a new isolated planning session and returns its trip ID.

### Send a trip message

```http
POST /trips/{trip_id}/messages
```

Example request:

```json
{
  "message": "I want to travel from Karachi to Istanbul."
}
```

### Read trip state

```http
GET /trips/{trip_id}
```

Returns the current structured and persisted `TripState`.

## Persistence Boundary

Tripzy does not couple its application layer directly to Supabase.

```text
Application
    |
    v
TripRepository
    |
    +--------------------------+
    |                          |
    v                          v
InMemoryTripRepository   SupabaseTripRepository
    |                          |
    v                          v
Tests                   Supabase PostgreSQL
```

This keeps deterministic tests independent of external infrastructure and prevents database-specific behavior from leaking throughout the application.

Persistence failures are translated into application-owned `TripRepositoryError` exceptions before reaching the API layer.

## CORS

Browser access is restricted to configured frontend origins.

Local defaults:

```text
http://localhost:3000
http://127.0.0.1:3000
```

Production frontend domains can be configured through `CORS_ORIGINS` without changing application code.

## Run Tests

```powershell
pytest -q
```

The test suite covers core workflow behavior as well as API contracts including:

- health checks
- trip creation
- persisted trip retrieval
- missing-trip responses
- request validation
- persistence failure handling
- CORS preflight behavior

## Current Status

Completed:

- conversational trip requirement collection
- runtime-aware date handling
- structured destination research
- structured flight research
- structured hotel research
- structured activity research
- deterministic itinerary validation
- structured day-by-day itinerary planning
- FastAPI backend
- Supabase PostgreSQL persistence
- persistence abstraction
- backend error boundaries
- configurable CORS
- deterministic backend/API tests

Next:

- frontend application
- frontend/backend integration
- Docker and deployment
- final end-to-end QA
- portfolio/demo polish

## Security Notes

Tripzy keeps Supabase privileged credentials on the backend.

The intended architecture is:

```text
Browser
   |
   v
FastAPI
   |
   v
TripRepository
   |
   v
Supabase
```

The frontend must not receive the Supabase secret key.

The `trips` table has Row Level Security enabled and is accessed through the trusted backend persistence layer.

## Project Goal

Tripzy is designed as a practical exercise in building an agentic product where probabilistic AI components operate inside deterministic software boundaries.

The goal is not to add multiple agents for their own sake. Each agent or workflow component should have a clear responsibility, while application code remains responsible for system truth.