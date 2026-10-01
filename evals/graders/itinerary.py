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
    expected: dict[str, Any],
) -> dict[str, Any]:
    start = date.fromisoformat(expected["start_date"])
    duration = expected["duration_days"]
    expected_dates = [
        (start + timedelta(days=offset)).isoformat()
        for offset in range(duration)
    ]
    days = itinerary.get("days", [])
    actual_dates = [day.get("date") for day in days]
    eligible = set(expected.get("eligible_activity_names", []))

    unknown_named = []
    total_cost = 0.0
    exposed_costs = False
    for day in days:
        for item in day.get("items", []):
            title = " ".join(str(item.get("title", "")).strip().split())
            normalized = title.casefold()
            if title and normalized not in GENERIC_TITLES and title not in eligible:
                unknown_named.append(title)
            cost = item.get("estimated_cost")
            if isinstance(cost, (int, float)):
                exposed_costs = True
                total_cost += float(cost)

    budget = expected.get("budget")
    budget_ok = True
    if budget is not None and exposed_costs:
        budget_ok = total_cost <= float(budget)

    checks = {
        "day_count": len(days) == duration,
        "dates_contiguous": actual_dates == expected_dates,
        "activities_researched": not unknown_named,
        "budget_adherence": budget_ok,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "unknown_named_activities": unknown_named,
        "exposed_cost_total": total_cost if exposed_costs else None,
    }
