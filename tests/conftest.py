import os


# app.api creates the production repository at import time. Tests replace it
# with deterministic doubles, but safe placeholders are still needed during
# collection on a clean checkout.
os.environ["APP_ENV"] = "development"
os.environ["CORS_ORIGINS"] = (
    "http://localhost:3000,http://127.0.0.1:3000"
)
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-placeholder-key")
