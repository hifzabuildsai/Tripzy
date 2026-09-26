import pytest

from app.models.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryItem,
)
from app.models.trip import TripRequest
from app.services.hotel_research import (
    HotelResearchService,
)
from app.services.itinerary_planning import (
    ItineraryPlannerService,
)


def build_valid_itinerary() -> Itinerary:
    """
    Return a valid deterministic itinerary fixture.

    No LLM or web calls are required.
    """

    return Itinerary(
        destination="Istanbul",
        start_date="2027-09-10",
        end_date="2027-09-14",
        travelers=2,
        days=[
            ItineraryDay(
                day_number=1,
                date="2027-09-10",
                title="Sultanahmet",
                items=[
                    ItineraryItem(
                        title="Basilica Cistern",
                        category="historical site",
                    ),
                    ItineraryItem(
                        title="Lunch",
                        category="meal",
                    ),
                ],
            ),
            ItineraryDay(
                day_number=2,
                date="2027-09-11",
                title="Markets",
                items=[
                    ItineraryItem(
                        title="Spice Bazaar",
                        category="market",
                    ),
                ],
            ),
            ItineraryDay(
                day_number=3,
                date="2027-09-12",
                title="Flexible Day",
                items=[
                    ItineraryItem(
                        title="Free Time",
                        category="free time",
                    ),
                ],
            ),
            ItineraryDay(
                day_number=4,
                date="2027-09-13",
                title="Rest Day",
                items=[
                    ItineraryItem(
                        title="Rest",
                        category="rest",
                    ),
                ],
            ),
            ItineraryDay(
                day_number=5,
                date="2027-09-14",
                title="Final Day",
                items=[
                    ItineraryItem(
                        title="Accommodation check-out",
                        category="generic",
                    ),
                ],
            ),
        ],
        planning_notes=[],
    )


def validate(
    itinerary: Itinerary,
) -> None:
    """
    Validate using the same application-owned invariants
    used by the production itinerary service.
    """

    ItineraryPlannerService._validate_itinerary(
        itinerary=itinerary,
        destination="Istanbul",
        start_date="2027-09-10",
        travelers=2,
        expected_dates=[
            "2027-09-10",
            "2027-09-11",
            "2027-09-12",
            "2027-09-13",
            "2027-09-14",
        ],
        eligible_activity_names=[
            "Basilica Cistern",
            "Spice Bazaar",
            "Kadıköy Market",
        ],
    )


def test_itinerary_dates_are_deterministic():
    dates = (
        ItineraryPlannerService
        ._build_itinerary_dates(
            start_date="2027-09-10",
            duration_days=5,
        )
    )

    assert dates == [
        "2027-09-10",
        "2027-09-11",
        "2027-09-12",
        "2027-09-13",
        "2027-09-14",
    ]


def test_hotel_checkout_uses_inclusive_trip_days():
    request = TripRequest(
        start_date="2027-09-10",
        duration_days=5,
    )

    check_out = (
        HotelResearchService
        ._resolve_check_out_date(
            request
        )
    )

    assert check_out == "2027-09-14"


def test_explicit_end_date_takes_precedence():
    request = TripRequest(
        start_date="2027-09-10",
        end_date="2027-09-20",
        duration_days=5,
    )

    check_out = (
        HotelResearchService
        ._resolve_check_out_date(
            request
        )
    )

    assert check_out == "2027-09-20"


def test_valid_itinerary_passes_validation():
    itinerary = build_valid_itinerary()

    validate(itinerary)


def test_wrong_destination_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.destination = "Paris"

    with pytest.raises(
        ValueError,
        match="destination",
    ):
        validate(itinerary)


def test_wrong_start_date_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.start_date = "2027-09-11"

    with pytest.raises(
        ValueError,
        match="start date",
    ):
        validate(itinerary)


def test_wrong_end_date_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.end_date = "2027-09-15"

    with pytest.raises(
        ValueError,
        match="end date",
    ):
        validate(itinerary)


def test_wrong_traveler_count_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.travelers = 3

    with pytest.raises(
        ValueError,
        match="traveler count",
    ):
        validate(itinerary)


def test_wrong_number_of_days_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.days.pop()

    with pytest.raises(
        ValueError,
        match="incorrect number",
    ):
        validate(itinerary)


def test_changed_calendar_date_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.days[2].date = "2027-09-20"

    with pytest.raises(
        ValueError,
        match="itinerary dates",
    ):
        validate(itinerary)


def test_wrong_day_sequence_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.days[1].day_number = 4

    with pytest.raises(
        ValueError,
        match="day sequence",
    ):
        validate(itinerary)


def test_unselected_flight_arrival_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.days[0].items.append(
        ItineraryItem(
            title="Flight Arrival",
            category="transport",
        )
    )

    with pytest.raises(
        ValueError,
        match="unselected flight",
    ):
        validate(itinerary)


def test_unselected_flight_departure_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.days[-1].items.append(
        ItineraryItem(
            title="Flight Departure",
            category="transport",
        )
    )

    with pytest.raises(
        ValueError,
        match="unselected flight",
    ):
        validate(itinerary)


def test_generic_planning_blocks_are_allowed():
    itinerary = build_valid_itinerary()

    itinerary.days[0].items.extend(
        [
            ItineraryItem(
                title="Breakfast",
                category="meal",
            ),
            ItineraryItem(
                title="Rest and Free Time",
                category="rest",
            ),
            ItineraryItem(
                title="Local Transfer",
                category="transport",
            ),
            ItineraryItem(
                title="Accommodation check-in",
                category="generic",
            ),
        ]
    )

    validate(itinerary)


def test_generic_local_transfer_is_allowed_without_research():
    itinerary = build_valid_itinerary()

    itinerary.days[0].items.append(
        ItineraryItem(
            title="Generic local transfer",
            category="logistics",
        )
    )

    validate(itinerary)


def test_generic_category_does_not_allow_invented_named_activity():
    itinerary = build_valid_itinerary()

    itinerary.days[2].items.append(
        ItineraryItem(
            title="Secret Bosphorus Lantern Museum",
            category="transport",
        )
    )

    with pytest.raises(
        ValueError,
        match="outside the structured activity research",
    ):
        validate(itinerary)


def test_activity_name_must_match_research_exactly():
    itinerary = build_valid_itinerary()

    itinerary.days[2].items.append(
        ItineraryItem(
            title="Kadıkcy Market",
            category="food experience",
        )
    )

    with pytest.raises(
        ValueError,
        match="outside the structured activity research",
    ):
        validate(itinerary)


def test_exact_unicode_activity_name_is_allowed():
    itinerary = build_valid_itinerary()

    itinerary.days[2].items.append(
        ItineraryItem(
            title="Kadıköy Market",
            category="food experience",
        )
    )

    validate(itinerary)


def test_destination_only_attraction_is_rejected():
    itinerary = build_valid_itinerary()

    itinerary.days[2].items.append(
        ItineraryItem(
            title="Hagia Sophia",
            category="historical site",
        )
    )

    with pytest.raises(
        ValueError,
        match="outside the structured activity research",
    ):
        validate(itinerary)
