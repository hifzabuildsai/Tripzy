import os

from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


# ============================================================
# APPLICATION
# ============================================================

APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}


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