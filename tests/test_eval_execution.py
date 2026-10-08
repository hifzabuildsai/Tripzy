import asyncio
from types import SimpleNamespace

import pytest

from evals import execution, run
from evals.graders import grade_itinerary


def test_transient_rate_limit_waits_before_retry(monkeypatch):
    sleeps, calls = [], []

    async def sleep(delay):
        sleeps.append(delay)

    async def model():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("429: Please retry in 41.5s")
        return "ok"

    monkeypatch.setattr(execution.asyncio, "sleep", sleep)
    assert asyncio.run(execution.with_retry(model)) == "ok"
    assert sleeps == [42.5]
    assert len(calls) == 2


def test_daily_quota_does_not_retry(monkeypatch):
    calls = []

    async def model():
        calls.append(1)
        raise RuntimeError("429 GenerateRequestsPerDayPerProjectPerModel-FreeTier")

    async def must_not_sleep(delay):
        raise AssertionError("daily quota cannot be fixed by a short wait")

    monkeypatch.setattr(execution.asyncio, "sleep", must_not_sleep)
    with pytest.raises(RuntimeError, match="PerDay"):
        asyncio.run(execution.with_retry(model))
    assert len(calls) == 1


def test_portfolio_selection_is_balanced_and_preserves_regression():
    for suite, count in (("intake_extraction", 20), ("correction_extraction", 30)):
        cases = run.load_cases(suite)
        selected = execution.select_portfolio_cases(cases)
        assert len(selected) == count
        assert selected == execution.select_portfolio_cases(cases)
        assert sum(case["language"] != "en" for case in selected) / count == 0.4
        assert {case["language"] for case in selected} == {case["language"] for case in cases}
        if suite == "correction_extraction":
            assert any("budget-only" in case["tags"] for case in selected)


def test_execution_failure_has_no_fake_quality_score():
    result = {
        "id": "failed", "suite": "intake_extraction", "repeat": 1,
        "passed": False, "metrics": {}, "error": "provider quota",
    }
    report = run.build_report([result], ("intake_extraction",), 1, "replay")
    suite = report["suites"]["intake_extraction"]
    assert suite["mean"]["field_precision"] is None
    assert suite["mean"]["unrequested_field_rate"] is None
    assert suite["metrics"]["field_precision"]["measured_trials"] == 0
    assert suite["mean"]["execution_success_rate"] == 0
    assert suite["failures"][0]["metric"] == "execution"


def test_missing_costs_are_unmeasured_not_budget_success():
    request = {"destination": "Istanbul", "start_date": "2027-09-10",
               "duration_days": 1, "travelers": 2, "budget": 100, "currency": "USD"}
    itinerary = {"destination": "Istanbul", "travelers": 2,
                 "days": [{"date": "2027-09-10", "items": [{"title": "Lunch"}]}]}
    research = {"activity_options": [], "hotel_options": [], "flight_options": []}
    assert grade_itinerary(itinerary, request, research)["checks"]["budget_adherence_when_exposed"] is None
    itinerary["days"][0]["items"][0].update(estimated_cost=200, currency="USD")
    assert grade_itinerary(itinerary, request, research)["checks"]["budget_adherence_when_exposed"] is False
    itinerary["days"][0]["items"][0]["currency"] = "TRY"
    assert grade_itinerary(itinerary, request, research)["checks"]["budget_adherence_when_exposed"] is None


def test_checkpoint_resumes_completed_quality_failures_and_retries_outages(monkeypatch, tmp_path):
    cases = run.load_cases("intake_extraction")[:2]
    monkeypatch.setattr(run, "load_cases", lambda suite: cases)
    calls = []
    fail_provider = True

    async def model(case):
        calls.append(case["id"])
        if case == cases[1] and fail_provider:
            raise RuntimeError("429 GenerateRequestsPerDayPerProjectPerModel-FreeTier")
        return {"passed": False, "metrics": {"field_precision": 0.5, "field_recall": 0.5,
                "unrequested_field_rate": 0.0}, "actual": {}, "expected": {}}

    monkeypatch.setitem(run.RUNNERS, "intake_extraction", model)
    args = SimpleNamespace(suite="intake_extraction", profile="full", repeat=1,
                           search_mode="replay", checkpoint=tmp_path / "checkpoint.json",
                           concurrency=1, request_interval=0)
    first = asyncio.run(run.async_main(args))
    assert first["evaluation"]["valid_baseline"] is False
    fail_provider = False
    calls.clear()
    second = asyncio.run(run.async_main(args))
    assert calls == [cases[1]["id"]]
    assert second["evaluation"]["valid_baseline"] is True
    assert second["suites"]["intake_extraction"]["mean"]["pass_rate"] == 0
    args.repeat = 2
    with pytest.raises(ValueError, match="Checkpoint does not match"):
        asyncio.run(run.async_main(args))
