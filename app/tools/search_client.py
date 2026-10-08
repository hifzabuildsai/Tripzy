import hashlib
import json
import os
from pathlib import Path
from typing import Any

from tavily import TavilyClient

from app.config import TAVILY_API_KEY


VALID_SEARCH_MODES = {"live", "record", "replay"}
DEFAULT_FIXTURE_DIR = (
    Path(__file__).resolve().parents[2]
    / "evals"
    / "fixtures"
    / "search"
)


class SearchReplayMissError(RuntimeError):
    """Raised when replay mode has no fixture for a search request."""


def _search_mode() -> str:
    mode = os.getenv("TRIPZY_SEARCH_MODE", "live").strip().lower()

    if mode not in VALID_SEARCH_MODES:
        raise RuntimeError(
            "TRIPZY_SEARCH_MODE must be one of: live, record, replay."
        )

    return mode


def _fixture_dir() -> Path:
    configured = os.getenv("TRIPZY_SEARCH_FIXTURE_DIR")

    if configured:
        return Path(configured)

    return DEFAULT_FIXTURE_DIR


def fixture_key(query: str, params: dict[str, Any]) -> str:
    """Return a stable content key for one search request."""

    payload = {
        "query": query,
        "params": params,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def _fixture_path(query: str, params: dict[str, Any]) -> Path:
    return _fixture_dir() / f"{fixture_key(query, params)}.json"


def _load_fixture(query: str, params: dict[str, Any]) -> dict[str, Any]:
    path = _fixture_path(query, params)

    if not path.is_file():
        raise SearchReplayMissError(
            "Replay fixture missing for search request "
            f"{fixture_key(query, params)}."
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    response = payload.get("response")

    if not isinstance(response, dict):
        raise RuntimeError(
            f"Invalid replay fixture format: {path.name}."
        )

    return response


def _record_fixture(
    query: str,
    params: dict[str, Any],
    response: dict[str, Any],
) -> None:
    path = _fixture_path(query, params)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "request": {
            "query": query,
            "params": params,
        },
        "response": response,
    }

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def search(query: str, **params: Any) -> dict[str, Any]:
    """Search through the production/live or deterministic eval seam."""

    mode = _search_mode()

    if mode == "replay":
        return _load_fixture(query, params)

    client = TavilyClient(api_key=TAVILY_API_KEY)
    response = client.search(query=query, **params)

    if not isinstance(response, dict):
        raise RuntimeError("Tavily search returned an unexpected response.")

    if mode == "record":
        _record_fixture(query, params, response)

    return response
