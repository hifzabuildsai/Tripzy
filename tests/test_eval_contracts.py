from evals.run import build_report, load_cases


def test_eval_dataset_sizes_and_multilingual_coverage():
    intake = load_cases("intake_extraction")
    corrections = load_cases("correction_extraction")
    itineraries = load_cases("itinerary_invariants")

    assert len(intake) == 40
    assert len(corrections) == 60
    assert len(itineraries) == 10

    intake_multilingual = [
        case for case in intake
        if case["language"] != "en"
    ]
    correction_multilingual = [
        case for case in corrections
        if case["language"] != "en"
    ]

    assert len(intake_multilingual) / len(intake) >= 0.30
    assert len(correction_multilingual) / len(corrections) >= 0.30

    regression = [
        case
        for case in corrections
        if "budget-only" in case.get("tags", [])
    ]
    assert len(regression) == 1
    assert regression[0]["input"]["message"] == (
        "Reduce the budget to $2,000."
    )


def test_report_matches_locked_schema():
    results = [
        {
            "id": "intake-001",
            "suite": "intake_extraction",
            "language": "en",
            "repeat": 1,
            "tags": [],
            "duration_ms": 1,
            "passed": True,
            "metrics": {
                "field_precision": 1.0,
                "field_recall": 1.0,
                "unrequested_field_rate": 0.0,
            },
            "expected": {"origin": "Karachi"},
            "actual": {"origin": "Karachi"},
            "error": None,
        }
    ]

    report = build_report(
        results=results,
        suites=("intake_extraction",),
        repeat_count=1,
        search_mode="replay",
    )

    assert report["schema_version"] == 1
    assert report["search_mode"] == "replay"
    assert set(report) == {
        "schema_version",
        "generated_at",
        "model",
        "search_mode",
        "repeat",
        "suites",
        "overall",
    }

    suite = report["suites"]["intake_extraction"]
    assert set(suite) == {
        "case_count",
        "repeat_count",
        "metrics",
        "mean",
        "min",
        "failures",
    }
    assert suite["case_count"] == 1
    assert suite["repeat_count"] == 1
    assert suite["failures"] == []
