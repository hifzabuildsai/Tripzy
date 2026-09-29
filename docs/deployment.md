# Tripzy Production Deployment

Tripzy is deployed as independently managed frontend, backend, and persistence services:

```text
Browser
  +-> Next.js frontend on Vercel
  |
  +-> FastAPI backend container on Railway
        +-> Supabase PostgreSQL
        +-> Gemini
        +-> Tavily
```

Gemini, Tavily, and Supabase credentials are backend-only. The browser receives
only `NEXT_PUBLIC_TRIPZY_API_URL`, which is intentionally public.

Docker Compose is not part of the production path. Vercel, Railway, and Supabase
manage their own services, so Compose would duplicate orchestration without
improving deployment fidelity.

## Current production endpoints

- Frontend: `https://tripzy-liard.vercel.app`
- Backend: `https://tripzy-api-production.up.railway.app`
- Backend health: `https://tripzy-api-production.up.railway.app/health`

The production browser origin allowed by the backend is:

```text
https://tripzy-liard.vercel.app
```

## Production environment contract

### Railway backend

| Variable | Required | Secret | Production value |
| --- | --- | --- | --- |
| `APP_ENV` | Yes | No | `production` |
| `GEMINI_API_KEY` | Yes | Yes | Gemini API key |
| `GEMINI_MODEL` | No | No | Defaults to `gemini-3.5-flash-lite` |
| `TAVILY_API_KEY` | Yes | Yes | Tavily API key |
| `SUPABASE_URL` | Yes | No | Project URL, such as `https://<project-ref>.supabase.co` |
| `SUPABASE_KEY` | Yes | Yes | Backend-only Supabase secret key |
| `CORS_ORIGINS` | Yes | No | Comma-separated exact frontend origins, without paths |
| `DEBUG` | No | No | Keep `false` in production |
| `PORT` | Platform-owned | No | Railway injects this; do not hard-code it |

When `APP_ENV=production`, the server refuses to start if any required backend
variable is empty. Production has no localhost CORS fallback. `CORS_ORIGINS`
must contain complete origins, for example:

```env
CORS_ORIGINS=https://tripzy-liard.vercel.app
```

Do not include a path or trailing slash. Do not use `*`.

### Vercel frontend

| Variable | Required | Secret | Production value |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_TRIPZY_API_URL` | Yes | No | `https://tripzy-api-production.up.railway.app` |

`NEXT_PUBLIC_` variables are compiled into the browser bundle. Changing the API
URL requires a new Vercel deployment. Never place Gemini, Tavily, or Supabase
credentials in Vercel frontend variables.

## Pre-deployment checks

Database bootstrap and deny-by-default RLS verification are documented in
[`docs/database.md`](database.md).

From the repository root:

```bash
python -m pip install --require-hashes --requirement requirements.lock
python -m pip install pytest==9.1.1
pytest -q
```

From `frontend/`:

```bash
npm ci
npm test
npm run lint
NEXT_PUBLIC_TRIPZY_API_URL=https://api.example.com npm run build
```

Build and smoke-test the backend image:

```bash
docker build --tag tripzy-backend:release-gate .
docker run --detach --rm --name tripzy-backend \
  --publish 8000:8000 \
  --env SUPABASE_URL=https://example.supabase.co \
  --env SUPABASE_KEY=local-smoke-test \
  tripzy-backend:release-gate
curl --fail --retry 10 --retry-all-errors http://127.0.0.1:8000/health
docker stop tripzy-backend
```

The local smoke test uses non-secret persistence placeholders because the
repository client is initialized when the API starts; `/health` does not make a
database request. A production-mode start must receive the complete Railway
environment contract and real credentials.

## Railway backend

1. Create a Railway project and service from the Tripzy GitHub repository.
2. Use the repository root and the root `Dockerfile`.
3. Do not override the image command. The container starts with
   `python -m app.server`.
4. Add the backend variables from the contract above. Keep credentials in
   Railway variables, never in source.
5. Set the health check path to `/health`.
6. Generate a Railway public domain.
7. Deploy the release branch for acceptance; after the release is merged, use
   `main` as the production source branch.
8. Verify the public endpoints over HTTPS:

   ```bash
   curl --fail https://tripzy-api-production.up.railway.app/health
   curl --fail https://tripzy-api-production.up.railway.app/
   ```

The server binds to `0.0.0.0` and reads Railway's injected `PORT`.

## Vercel frontend

1. Import the Tripzy GitHub repository.
2. Set the project root directory to `frontend`.
3. Use the detected **Next.js** framework settings and normal production build.
4. Add `NEXT_PUBLIC_TRIPZY_API_URL=https://tripzy-api-production.up.railway.app`
   to the Production environment.
5. Deploy the release branch for acceptance; after the release is merged, use
   `main` as the production branch.
6. If the final Vercel production origin changes, update `CORS_ORIGINS` on
   Railway and redeploy the backend.

## Live acceptance checks

M17 live acceptance verified the following production behavior:

1. The Vercel frontend can create and load a persisted trip through Railway.
2. Refresh and direct trip URLs restore the same durable Supabase-backed trip.
3. A destination revision from Istanbul to Tokyo keeps the same trip ID and
   re-runs destination, flight, hotel, activity, and itinerary planning.
4. Tavily executes successfully in production for destination, flight, hotel,
   and activity research.
5. An intentional model failure returns a retry-safe error without overwriting
   the prior persisted Tokyo plan.
6. Restoring the valid model and retrying the correction succeeds and persists
   the revised budget.
7. Browser-to-backend requests use HTTPS with the exact configured CORS origin.

Backend credentials must remain absent from the browser bundle, request payloads,
and Vercel frontend environment settings.

## Rollback boundary

Railway and Vercel can roll back independently. If a frontend release fails,
restore the prior Vercel deployment without changing the backend. If the API
release fails, restore the prior Railway deployment while leaving the frontend
API URL unchanged.
