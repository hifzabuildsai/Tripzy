from datetime import date, timedelta
from typing import Any


GENERIC_TITLES = {
    "breakfast",
    "lunch",
    "dinner",
    "meal",
    "rest",
    "rest and free time",
    "free time",
    "leisure time",
    "local transfer",
    "generic local transfer",
    "accommodation check-in",
    "accommodation check-out",
    "hotel check-in",
    "hotel check-out",
    "check-in",
    "check-out",
}


def grade_itinerary(
    itinerary: dict[str, Any],
    trip_request: dict[str, Any],
    research: dict[str, Any],
) -> dict[str, Any]:
    """Grade deterministic itinerary invariants against replayed research."""

    start = date.fromisoformat(trip_request["start_date"])
    duration = trip_request["duration_days"]
    expected_dates = [
        (start + timedelta(days=offset)).isoformat()
        for offset in range(duration)
    ]
    days = itinerary.get("days", [])
    actual_dates = [day.get("date") for day in days]

    activity_options = research.get("activity_options", [])
    eligible_names = {
        option["name"]
        for option in activity_options
        if option.get("name")
    }
    hotel_names = {
        option["name"].casefold()
        for option in research.get("hotel_options", [])
        if option.get("name")
    }
    airline_names = {
        option["airline"].casefold()
        for option in research.get("flight_options", [])
        if option.get("airline")
    }

    unknown_named: list[str] = []
    candidate_selection_mentions: list[str] = []
    exposed_cost_total = 0.0
    exposed_costs = False
    comparable_costs = True

    for day in days:
        for item in day.get("items", []):
            title = " ".join(str(item.get("title", "")).strip().split())
            normalized = title.casefold()

            if (
                title
                and normalized not in GENERIC_TITLES
                and title not in eligible_names
            ):
                unknown_named.append(title)

            haystack = " ".join(
                str(item.get(key) or "")
                for key in ("title", "description")
            ).casefold()
            if any(name in haystack for name in hotel_names | airline_names):
                candidate_selection_mentions.append(title or haystack)

            cost = item.get("estimated_cost")
            if isinstance(cost, (int, float)):
                exposed_costs = True
                if item.get("currency") != trip_request.get("currency") or cost < 0:
                    comparable_costs = False
                exposed_cost_total += float(cost)

    budget = trip_request.get("budget")
    budget_ok = None
    if budget is not None and exposed_costs and comparable_costs:
        budget_ok = exposed_cost_total <= float(budget)

    checks = {
        "day_count_equals_duration": len(days) == duration,
        "dates_contiguous": actual_dates == expected_dates,
        "destination_matches": (
            itinerary.get("destination") == trip_request["destination"]
        ),
        "travelers_match": (
            itinerary.get("travelers") == trip_request["travelers"]
        ),
        "named_activities_researched": not unknown_named,
        "candidates_not_selected": not candidate_selection_mentions,
        "budget_adherence_when_exposed": budget_ok,
    }

    return {
        "passed": all(value for value in checks.values() if value is not None),
        "checks": checks,
        "unknown_named_activities": unknown_named,
        "candidate_selection_mentions": candidate_selection_mentions,
        "exposed_cost_total": (
            exposed_cost_total if exposed_costs else None
        ),
    }
