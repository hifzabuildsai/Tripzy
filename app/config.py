import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from agents import (
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)

load_dotenv()


# ============================================================
# OPENAI AGENTS SDK
# ============================================================

# Tripzy currently uses Gemini for model inference.
#
# The OpenAI Agents SDK enables OpenAI trace exporting by
# default. Because we are not using an OpenAI API key for
# tracing, disable trace export globally.
#
# This does NOT disable:
# - Gemini inference
# - agents
# - tools
# - handoffs
# - Tavily
#
# It only disables OpenAI trace collection/export.

set_tracing_disabled(True)


# -------------------------
# Gemini
# -------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
)

gemini_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

gemini_model = OpenAIChatCompletionsModel(
    model=GEMINI_MODEL,
    openai_client=gemini_client,
)


# -------------------------
# Tavily
# -------------------------

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is not set")