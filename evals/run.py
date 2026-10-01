import argparse
import asyncio
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.state import TripState
from app.models.trip import TripRequest
from app.services.conversation import ConversationService
from app.services.itinerary_planning import ItineraryPlannerService
from app.tools.search_client import search
from evals.graders import grade_fields, grade_itinerary


ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT / "datasets"
REPORT_DIR = ROOT / "reports"

SUITES = (
    "intake_extraction",
    "correction_extraction",
    "itinerary_invariants",
)

SUITE_METRICS = {
    "intake_extraction": (
        "field_precision",
        "field_recall",
        "unrequested_field_rate",
    ),
    "correction_extraction": (
        "exact_match",
        "unrequested_field_rate",
        "interest_operation_correctness",
    ),
    "itinerary_invariants": (
        "day_count_equals_duration",
        "dates_contiguous",
        "destination_matches",
        "travelers_match",
        "named_activities_researched",
        "candidates_not_selected",
        "budget_adherence_when_exposed",
    ),
}


def load_cases(suite: str) -> list[dict[str, Any]]:
    path = DATASET_DIR / f"{suite}.jsonl"
    cases = []

    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw.strip():
            continue

        case = json.loads(raw)
        if case.get("suite") != suite:
            raise ValueError(
                f"{path.name}:{line_number} has the wrong suite."
            )
        cases.append(case)

    return cases


def _is_rate_limit(error: Exception) -> bool:
    message = str(error).casefold()
    return any(
        marker in message
        for marker in (
            "429",
            "rate limit",
            "resource_exhausted",
            "resource exhausted",
            "quota",
        )
    )


async def _with_retry(factory, attempts: int = 4):
    for attempt in range(attempts):
        try:
            return await factory()
        except Exception as error:
            if not _is_rate_limit(error) or attempt == attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)

    raise RuntimeError("unreachable")


async def run_intake(case: dict[str, Any]) -> dict[str, Any]:
    current = case["input"].get("current_request") or {}
    service = ConversationService(
        state=TripState(request=TripRequest(**current))
    )
    captured: dict[str, Any] = {}
    original_update = service.trip_manager.update_request_fields

    def capture_update(**fields):
        captured.update(fields)
        original_update(**fields)

    async def stop_before_research():
        return "__eval_stop__"

    service.trip_manager.update_request_fields = capture_update
    service._continue_workflow = stop_before_research

    for message in case["input"]["messages"]:
        await service.process_message(message)

    grade = grade_fields(
        captured,
        case["expected"]["fields"],
    )

    return {
        "passed": grade["passed"],
        "metrics": {
            "field_precision": grade["field_precision"],
            "field_recall": grade["field_recall"],
            "unrequested_field_rate": grade["unrequested_field_rate"],
        },
        "actual": captured,
        "expected": case["expected"]["fields"],
    }


async def run_correction(case: dict[str, Any]) -> dict[str, Any]:
    state = TripState(
        request=TripRequest(**case["input"]["current_request"]),
        status="itinerary_planned",
    )
    service = ConversationService(state=state)

    correction = await service._interpret_correction(
        case["input"]["message"]
    )
    actual = correction.model_dump(
        exclude_none=True,
        exclude_defaults=True,
    )
    expected = case["expected"]["correction"]
    grade = grade_fields(actual, expected)

    return {
        "passed": grade["passed"],
        "metrics": {
            "exact_match": grade["exact_match"],
            "unrequested_field_rate": grade["unrequested_field_rate"],
            "interest_operation_correctness": (
                grade["interest_operation_correctness"]
            ),
        },
        "actual": actual,
        "expected": expected,
    }


async def run_itinerary(case: dict[str, Any]) -> dict[str, Any]:
    fixture_response = search(
        f"eval itinerary research {case['id']}",
        fixture_type="itinerary_research",
    )
    research = fixture_response.get("research")

    if not isinstance(research, dict):
        raise ValueError(
            f"Replay research fixture is invalid for {case['id']}."
        )

    trip_request = case["input"]["trip_request"]
    state = TripState.model_validate({
        "request": trip_request,
        "destination_research": research.get("destination_research"),
        "flight_options": research.get("flight_options", []),
        "hotel_options": research.get("hotel_options", []),
        "activity_options": research.get("activity_options", []),
        "status": "activities_researched",
    })

    itinerary = await ItineraryPlannerService().build_itinerary(state)
    actual = itinerary.model_dump()
    grade = grade_itinerary(
        actual,
        trip_request,
        research,
    )

    return {
        "passed": grade["passed"],
        "metrics": {
            key: 1.0 if value else 0.0
            for key, value in grade["checks"].items()
        },
        "actual": actual,
        "expected": case["expected"]["assertions"],
    }


RUNNERS = {
    "intake_extraction": run_intake,
    "correction_extraction": run_correction,
    "itinerary_invariants": run_itinerary,
}


async def run_case(
    case: dict[str, Any],
    repeat_index: int,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    started = time.monotonic()

    async with semaphore:
        try:
            outcome = await _with_retry(
                lambda: RUNNERS[case["suite"]](case)
            )
            error = None
        except Exception as exc:
            outcome = {
                "passed": False,
                "metrics": {},
                "expected": None,
                "actual": None,
            }
            error = f"{type(exc).__name__}: {exc}"

    return {
        "id": case["id"],
        "suite": case["suite"],
        "language": case["language"],
        "repeat": repeat_index + 1,
        "tags": case.get("tags", []),
        "duration_ms": round((time.monotonic() - started) * 1000),
        "passed": bool(outcome["passed"]),
        "metrics": outcome["metrics"],
        "expected": outcome["expected"],
        "actual": outcome["actual"],
        "error": error,
    }


def _metric_target(metric: str) -> float:
    return 0.0 if metric == "unrequested_field_rate" else 1.0


def _metric_failed(metric: str, value: float) -> bool:
    target = _metric_target(metric)
    return value > target if target == 0.0 else value < target


def _suite_report(
    suite: str,
    results: list[dict[str, Any]],
    repeat_count: int,
) -> dict[str, Any]:
    suite_results = [item for item in results if item["suite"] == suite]
    metrics = SUITE_METRICS[suite]
    repeat_aggregates: dict[str, list[float]] = {
        metric: []
        for metric in metrics
    }
    repeat_pass_rates: list[float] = []

    for repeat in range(1, repeat_count + 1):
        items = [
            item
            for item in suite_results
            if item["repeat"] == repeat
        ]
        repeat_pass_rates.append(
            sum(1 for item in items if item["passed"]) / len(items)
        )

        for metric in metrics:
            values = [
                float(item["metrics"][metric])
                for item in items
                if metric in item["metrics"]
            ]
            repeat_aggregates[metric].append(
                statistics.mean(values) if values else 0.0
            )

    failures = []
    for item in suite_results:
        if item["error"]:
            failures.append({
                "case_id": item["id"],
                "repeat": item["repeat"],
                "metric": "execution",
                "expected": "success",
                "actual": item["error"],
            })
            continue

        for metric in metrics:
            value = float(item["metrics"][metric])
            if _metric_failed(metric, value):
                failures.append({
                    "case_id": item["id"],
                    "repeat": item["repeat"],
                    "metric": metric,
                    "expected": _metric_target(metric),
                    "actual": value,
                })

    metric_contract = {
        metric: {
            "target": _metric_target(metric),
            "direction": (
                "lower" if metric == "unrequested_field_rate" else "higher"
            ),
        }
        for metric in metrics
    }
    metric_contract["pass_rate"] = {
        "target": 1.0,
        "direction": "higher",
    }

    mean = {
        metric: statistics.mean(values)
        for metric, values in repeat_aggregates.items()
    }
    minimum = {
        metric: min(values)
        for metric, values in repeat_aggregates.items()
    }
    mean["pass_rate"] = statistics.mean(repeat_pass_rates)
    minimum["pass_rate"] = min(repeat_pass_rates)

    return {
        "case_count": len(suite_results) // repeat_count,
        "repeat_count": repeat_count,
        "metrics": metric_contract,
        "mean": mean,
        "min": minimum,
        "failures": failures,
    }


def build_report(
    results: list[dict[str, Any]],
    suites: tuple[str, ...],
    repeat_count: int,
    search_mode: str,
) -> dict[str, Any]:
    suite_reports = {
        suite: _suite_report(
            suite,
            results,
            repeat_count,
        )
        for suite in suites
    }

    repeat_pass_rates = []
    for repeat in range(1, repeat_count + 1):
        items = [item for item in results if item["repeat"] == repeat]
        repeat_pass_rates.append(
            sum(1 for item in items if item["passed"]) / len(items)
        )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        "search_mode": search_mode,
        "repeat": repeat_count,
        "suites": suite_reports,
        "overall": {
            "case_count": len(results) // repeat_count,
            "repeat_count": repeat_count,
            "mean": {
                "pass_rate": statistics.mean(repeat_pass_rates),
            },
            "min": {
                "pass_rate": min(repeat_pass_rates),
            },
        },
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Tripzy eval report",
        "",
        f"- Model: `{report['model']}`",
        f"- Search mode: `{report['search_mode']}`",
        f"- Repeats: {report['repeat']}",
        "",
        "| Suite | Cases | Mean pass | Min pass | Failures |",
        "|---|---:|---:|---:|---:|",
    ]

    for suite, data in report["suites"].items():
        lines.append(
            "| "
            + " | ".join([
                suite,
                str(data["case_count"]),
                f"{data['mean']['pass_rate'] * 100:.1f}%",
                f"{data['min']['pass_rate'] * 100:.1f}%",
                str(len(data["failures"])),
            ])
            + " |"
        )

    lines.extend([
        "",
        "## Per-case failures",
        "",
    ])

    failures = [
        (suite, failure)
        for suite, data in report["suites"].items()
        for failure in data["failures"]
    ]

    if not failures:
        lines.append("None.")
    else:
        for suite, failure in failures:
            lines.append(
                f"- `{failure['case_id']}` repeat {failure['repeat']} "
                f"({suite}) — {failure['metric']}: expected "
                f"`{failure['expected']}`, actual "
                f"`{failure['actual']}`"
            )

    return "\n".join(lines) + "\n"


async def async_main(args) -> dict[str, Any]:
    os.environ["TRIPZY_SEARCH_MODE"] = args.search_mode

    suites = SUITES if args.suite == "all" else (args.suite,)
    cases = [
        case
        for suite in suites
        for case in load_cases(suite)
    ]

    semaphore = asyncio.Semaphore(args.concurrency)
    tasks = [
        run_case(case, repeat_index, semaphore)
        for repeat_index in range(args.repeat)
        for case in cases
    ]
    results = await asyncio.gather(*tasks)

    return build_report(
        results=results,
        suites=suites,
        repeat_count=args.repeat,
        search_mode=args.search_mode,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Tripzy evaluation suites."
    )
    parser.add_argument(
        "--suite",
        choices=("all",) + SUITES,
        default="all",
    )
    parser.add_argument(
        "--search-mode",
        choices=("live", "record", "replay"),
        default="replay",
    )
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be >= 1")
    if args.concurrency < 1 or args.concurrency > 2:
        parser.error("--concurrency must be 1 or 2")

    return args


def main():
    args = parse_args()
    report = asyncio.run(async_main(args))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stem = (
        args.output
        if args.output
        else REPORT_DIR / (
            f"{args.suite}-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        )
    )
    json_path = stem.with_suffix(".json")
    md_path = stem.with_suffix(".md")

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        markdown_report(report),
        encoding="utf-8",
    )

    print(json.dumps(report["suites"], indent=2))
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")

    execution_failures = [
        failure
        for suite in report["suites"].values()
        for failure in suite["failures"]
        if failure["metric"] == "execution"
    ]
    if execution_failures:
        raise SystemExit(
            "Eval execution failed for "
            f"{len(execution_failures)} case run(s); "
            "report was written but is not a valid baseline."
        )


if __name__ == "__main__":
    main()
