import os
from urllib.parse import urlsplit

from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


# ============================================================
# APPLICATION
# ============================================================

APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}

LOCAL_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)

PRODUCTION_REQUIRED_ENV_VARS = (
    "GEMINI_API_KEY",
    "TAVILY_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "CORS_ORIGINS",
)


def is_production() -> bool:
    return os.getenv("APP_ENV", "development").strip().lower() == "production"


def get_cors_origins() -> list[str]:
    """Return exact browser origins allowed to call the API."""

    configured_origins = os.getenv("CORS_ORIGINS")

    if configured_origins is None:
        if is_production():
            return []

        return list(LOCAL_CORS_ORIGINS)

    origins = [
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    ]

    for origin in origins:
        parsed = urlsplit(origin)
        is_http_origin = (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
            and not parsed.path
            and not parsed.query
            and not parsed.fragment
        )

        if not is_http_origin:
            raise RuntimeError(
                "CORS_ORIGINS must contain only comma-separated HTTP(S) origins."
            )

    return origins


def validate_production_environment() -> None:
    """Fail startup when a production-only dependency is unconfigured."""

    if not is_production():
        return

    missing = [
        variable
        for variable in PRODUCTION_REQUIRED_ENV_VARS
        if not os.getenv(variable, "").strip()
    ]

    if missing:
        raise RuntimeError(
            "Missing required production environment variables: "
            + ", ".join(missing)
        )

    origins = get_cors_origins()

    if "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS must use exact frontend origins in production."
        )


# ============================================================
# OPENAI AGENTS SDK
# ============================================================

# Tripzy uses Gemini for model inference through its
# OpenAI-compatible API endpoint.
#
# OpenAI trace exporting is disabled because Tripzy does not
# use an OpenAI API key for tracing.

set_tracing_disabled(True)


# ============================================================
# GEMINI
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

gemini_client = (
    AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    if GEMINI_API_KEY
    else None
)

gemini_model = (
    OpenAIChatCompletionsModel(
        model=GEMINI_MODEL,
        openai_client=gemini_client,
    )
    if gemini_client
    else None
)


# ============================================================
# TAVILY
# ============================================================

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
