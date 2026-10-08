from evals.graders import grade_fields, grade_itinerary


def test_grade_fields_reports_exact_match():
    result = grade_fields(
        {"budget": 2000, "currency": "USD"},
        {"budget": 2000, "currency": "USD"},
    )

    assert result["passed"] is True
    assert result["field_precision"] == 1.0
    assert result["field_recall"] == 1.0
    assert result["unrequested_field_rate"] == 0.0


def test_grade_fields_penalizes_unrequested_fields():
    result = grade_fields(
        {
            "budget": 2000,
            "currency": "USD",
            "interests_replace": [],
        },
        {
            "budget": 2000,
            "currency": "USD",
        },
    )

    assert result["passed"] is True
    assert result["unexpected_fields"] == []
    assert result["unrequested_field_rate"] == 0.0
    assert result["interest_operation_correctness"] == 1.0


def test_grade_fields_penalizes_nonempty_unrequested_fields():
    result = grade_fields(
        {
            "budget": 2000,
            "currency": "USD",
            "travel_style": "luxury",
        },
        {
            "budget": 2000,
            "currency": "USD",
        },
    )

    assert result["passed"] is False
    assert result["unexpected_fields"] == ["travel_style"]


def test_grade_itinerary_checks_research_boundary_and_dates():
    itinerary = {
        "days": [
            {
                "date": "2027-09-10",
                "items": [
                    {"title": "Basilica Cistern", "estimated_cost": 20, "currency": "USD"},
                    {"title": "Lunch"},
                ],
            },
            {
                "date": "2027-09-11",
                "items": [{"title": "Free Time"}],
            },
        ]
    }
    trip_request = {
        "destination": "Istanbul",
        "start_date": "2027-09-10",
        "duration_days": 2,
        "travelers": 2,
        "budget": 100,
        "currency": "USD",
    }
    research = {
        "activity_options": [{"name": "Basilica Cistern"}],
        "flight_options": [],
        "hotel_options": [],
    }
    itinerary["destination"] = "Istanbul"
    itinerary["travelers"] = 2

    result = grade_itinerary(itinerary, trip_request, research)

    assert result["passed"] is True
    assert all(result["checks"].values())


def test_grade_itinerary_rejects_unresearched_activity():
    itinerary = {
        "days": [
            {
                "date": "2027-09-10",
                "items": [{"title": "Invented Museum"}],
            },
        ]
    }
    trip_request = {
        "destination": "Istanbul",
        "start_date": "2027-09-10",
        "duration_days": 1,
        "travelers": 2,
    }
    research = {
        "activity_options": [],
        "flight_options": [],
        "hotel_options": [],
    }
    itinerary["destination"] = "Istanbul"
    itinerary["travelers"] = 2

    result = grade_itinerary(itinerary, trip_request, research)

    assert result["passed"] is False
    assert result["unknown_named_activities"] == ["Invented Museum"]
