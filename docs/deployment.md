# Tripzy Production Deployment

Tripzy deploys as two independently managed services:

```text
Browser
  -> Next.js frontend on Vercel
  -> FastAPI backend container on Render
  -> Supabase PostgreSQL

FastAPI
  -> Gemini
  -> Tavily
```

Gemini, Tavily, and Supabase credentials are backend-only. The browser receives
only `NEXT_PUBLIC_TRIPZY_API_URL`, which is intentionally public.

Docker Compose is not part of the production path. Vercel, Render, and Supabase
each manage their own service, so Compose would duplicate orchestration without
improving deployment fidelity.

## Production environment contract

### Render backend

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
| `PORT` | Platform-owned | No | Render injects this; do not hard-code it |

When `APP_ENV=production`, the server refuses to start if any required backend
variable is empty. Production has no localhost CORS fallback. `CORS_ORIGINS`
must contain complete origins, for example:

```env
CORS_ORIGINS=https://tripzy.vercel.app,https://www.example.com
```

Do not include a path or trailing slash. Do not use `*`.

### Vercel frontend

| Variable | Required | Secret | Production value |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_TRIPZY_API_URL` | Yes | No | Public HTTPS URL of the Render service, without a trailing slash |

`NEXT_PUBLIC_` variables are compiled into the browser bundle. Changing the API
URL requires a new Vercel deployment. Never place Gemini, Tavily, or Supabase
credentials in Vercel frontend variables.

## Pre-deployment checks

From the repository root:

```bash
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
docker build --tag tripzy-backend:m17 .
docker run --detach --rm --name tripzy-backend \
  --publish 8000:8000 \
  --env SUPABASE_URL=https://example.supabase.co \
  --env SUPABASE_KEY=local-smoke-test \
  tripzy-backend:m17
curl --fail --retry 10 --retry-all-errors http://127.0.0.1:8000/health
docker stop tripzy-backend
```

The local smoke test uses non-secret persistence placeholders because the
repository client is initialized when the API starts; `/health` does not make a
database request. A production-mode start must receive the complete Render
environment contract and real credentials.

## Render backend

1. Create a Render **Web Service** from the Tripzy GitHub repository.
2. Select the deployment branch intended for release.
3. Choose **Docker** as the runtime. Keep the repository root as the root
   directory and use the root `Dockerfile`.
4. Do not override the Docker command. The image starts `python -m app.server`.
5. Add the Render backend variables from the contract above. Use Render secret
   values for all credentials.
6. Set the health check path to `/health`.
7. Deploy and wait for the service to report healthy.
8. Verify these public endpoints over HTTPS:

   ```bash
   curl --fail https://<render-service>.onrender.com/health
   curl --fail https://<render-service>.onrender.com/
   ```

The server binds to `0.0.0.0` and reads the port injected by Render.

## Vercel frontend

1. Import the same GitHub repository into Vercel.
2. Set the project root directory to `frontend`.
3. Keep the detected **Next.js** framework settings and the normal production
   build command.
4. Add `NEXT_PUBLIC_TRIPZY_API_URL` with the Render HTTPS origin. Apply it to the
   Production environment (and Preview only when previews should call that API).
5. Deploy the selected release branch.
6. If the final Vercel production origin differs from the value already allowed
   by Render, update `CORS_ORIGINS` on Render and redeploy the backend.

## Live acceptance checks

After both deployments are healthy:

1. Open the Vercel production URL and create a new trip.
2. Complete the consolidated mission intake and wait for a plan.
3. Refresh the trip URL and confirm the same persisted trip returns.
4. Submit a revision and confirm the existing M16 failure/retry behavior remains
   intact.
5. In browser developer tools, confirm API requests use the Render HTTPS origin
   and have no mixed-content or CORS errors.
6. Confirm no backend credential appears in the browser bundle, request payloads,
   or Vercel frontend environment settings.

## Rollback boundary

Render and Vercel can roll back independently. If a frontend release fails,
restore the prior Vercel deployment without changing the backend. If the API
release fails, restore the prior Render deploy while leaving the frontend URL
unchanged.
