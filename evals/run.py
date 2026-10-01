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
from evals.graders import grade_fields, grade_itinerary


ROOT = Path(__file__).resolve().parent
DATASET_DIR = ROOT / "datasets"
REPORT_DIR = ROOT / "reports"

SUITES = (
    "intake_extraction",
    "correction_extraction",
    "itinerary_invariants",
)


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

    return grade_fields(
        captured,
        case["expected"]["fields"],
    ) | {"actual": captured}


async def run_correction(case: dict[str, Any]) -> dict[str, Any]:
    state = TripState(
        request=TripRequest(**case["input"]["current_request"]),
        status="itinerary_planned",
    )
    service = ConversationService(state=state)
    correction = await service._interpret_correction(
        case["input"]["utterance"]
    )
    actual = correction.model_dump(
        exclude_none=True,
        exclude_defaults=True,
    )

    return grade_fields(
        actual,
        case["expected"]["fields"],
    ) | {"actual": actual}


async def run_itinerary(case: dict[str, Any]) -> dict[str, Any]:
    state = TripState.model_validate(case["input"]["state"])
    itinerary = await ItineraryPlannerService().build_itinerary(state)
    actual = itinerary.model_dump()

    return grade_itinerary(
        actual,
        case["expected"],
    ) | {"actual": actual}


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
            result = await _with_retry(
                lambda: RUNNERS[case["suite"]](case)
            )
            error = None
        except Exception as exc:
            result = {"passed": False}
            error = f"{type(exc).__name__}: {exc}"

    return {
        "id": case["id"],
        "suite": case["suite"],
        "language": case["language"],
        "repeat": repeat_index + 1,
        "tags": case.get("tags", []),
        "duration_ms": round((time.monotonic() - started) * 1000),
        "passed": bool(result.get("passed")),
        "metrics": {
            key: value
            for key, value in result.items()
            if key not in {"actual", "passed"}
        },
        "actual": result.get("actual"),
        "error": error,
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    suites: dict[str, Any] = {}
    for suite in SUITES:
        suite_results = [r for r in results if r["suite"] == suite]
        if not suite_results:
            continue

        repeats = sorted({r["repeat"] for r in suite_results})
        repeat_scores = []
        for repeat in repeats:
            items = [r for r in suite_results if r["repeat"] == repeat]
            repeat_scores.append(
                sum(1 for item in items if item["passed"]) / len(items)
            )

        suites[suite] = {
            "runs": len(suite_results),
            "cases_per_repeat": len(suite_results) // len(repeats),
            "pass_rate_mean": statistics.mean(repeat_scores),
            "pass_rate_min": min(repeat_scores),
            "repeat_pass_rates": repeat_scores,
            "failed_case_ids": sorted({
                r["id"] for r in suite_results if not r["passed"]
            }),
        }

        if suite in {"intake_extraction", "correction_extraction"}:
            requested = [
                r["metrics"].get("unrequested_field_rate", 0.0)
                for r in suite_results
                if not r["error"]
            ]
            suites[suite]["unrequested_field_rate_mean"] = (
                statistics.mean(requested) if requested else None
            )

    return suites


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Tripzy eval report",
        "",
        f"- Model: `{report['model']}`",
        f"- Search mode: `{report['search_mode']}`",
        f"- Repeats: {report['repeat']}",
        "",
        "| Suite | Mean pass | Min pass | Unrequested fields | Failed cases |",
        "|---|---:|---:|---:|---:|",
    ]

    for suite, summary in report["summary"].items():
        unrequested = summary.get("unrequested_field_rate_mean")
        unrequested_text = (
            f"{unrequested * 100:.1f}%" if unrequested is not None else "—"
        )
        lines.append(
            "| "
            + " | ".join([
                suite,
                f"{summary['pass_rate_mean'] * 100:.1f}%",
                f"{summary['pass_rate_min'] * 100:.1f}%",
                unrequested_text,
                str(len(summary["failed_case_ids"])),
            ])
            + " |"
        )

    failures = [result for result in report["results"] if not result["passed"]]
    lines.extend(["", "## Per-case failures", ""])
    if not failures:
        lines.append("None.")
    else:
        for failure in failures:
            detail = failure["error"] or json.dumps(
                failure["metrics"],
                ensure_ascii=False,
                sort_keys=True,
            )
            lines.append(
                f"- `{failure['id']}` repeat {failure['repeat']} "
                f"({failure['language']}): {detail}"
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

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        "search_mode": args.search_mode,
        "repeat": args.repeat,
        "concurrency": args.concurrency,
        "summary": summarize(results),
        "results": results,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Run Tripzy evaluation suites.")
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
            f"{args.suite}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        )
    )
    json_path = stem.with_suffix(".json")
    md_path = stem.with_suffix(".md")

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(markdown_report(report), encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")


if __name__ == "__main__":
    main()
