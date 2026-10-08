"""Quota-aware evaluation execution; production agent behavior is unchanged."""
import asyncio
import re
import sys
from importlib.metadata import version
from collections import defaultdict


def daily_quota_exhausted(error):
    message = str(error).casefold()
    return any(marker in message for marker in (
        "requestsperday", "requests_per_day", "per day", "daily quota exhausted",
    ))


def is_rate_limit(error):
    return any(marker in str(error).casefold() for marker in (
        "429", "rate limit", "resource_exhausted", "resource exhausted", "quota",
    ))


def retry_delay(error):
    message = str(error)
    match = re.search(r"retry in ([0-9.]+)s", message, re.IGNORECASE)
    if not match:
        match = re.search(r"retryDelay[^0-9]+([0-9.]+)s", message)
    return min(60.0, max(1.0, float(match.group(1)) + 1)) if match else 35.0


async def with_retry(factory, attempts=4):
    for attempt in range(attempts):
        try:
            return await factory()
        except Exception as error:
            rate_limited = is_rate_limit(error)
            server_error = 500 <= getattr(error, "status_code", 0) < 600
            if daily_quota_exhausted(error) or not (rate_limited or server_error) or attempt == attempts - 1:
                raise
            await asyncio.sleep(retry_delay(error) if rate_limited else 2 ** attempt)
    raise RuntimeError("unreachable")


def select_portfolio_cases(cases):
    """Fixed balanced subset selected before looking at model outputs."""
    if cases[0]["suite"] == "itinerary_invariants":
        return cases
    target = 20 if cases[0]["suite"] == "intake_extraction" else 30
    english = [case for case in cases if case["language"] == "en"]
    mandatory = [case for case in english if "budget-only" in case.get("tags", [])]
    selected = mandatory + [case for case in english if case not in mandatory][:target * 3 // 5 - len(mandatory)]
    groups = defaultdict(list)
    for case in cases:
        if case["language"] != "en":
            groups[case["language"]].append(case)
    while len(selected) < target:
        for language in sorted(groups):
            if groups[language] and len(selected) < target:
                selected.append(groups[language].pop(0))
    ids = {case["id"] for case in selected}
    return [case for case in cases if case["id"] in ids]


def runtime_environment():
    return {
        "python": sys.version.split()[0],
        "packages": {name: version(name) for name in (
            "openai", "openai-agents", "pydantic", "tavily-python",
        )},
    }
