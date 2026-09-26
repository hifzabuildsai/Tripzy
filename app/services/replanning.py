from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.models.correction import TripCorrection
from app.models.state import TripState
from app.models.trip import TripRequest


Artifact = Literal[
    "destination_research",
    "flight_options",
    "hotel_options",
    "activity_options",
    "itinerary",
]

ARTIFACT_ORDER: tuple[Artifact, ...] = (
    "destination_research",
    "flight_options",
    "hotel_options",
    "activity_options",
    "itinerary",
)

# This graph mirrors the arguments and state consumed by the current service
# implementations. It is deliberately centralized so selective replanning can
# be reviewed and tested without following status mutations through the
# conversation coordinator.
DIRECT_FIELD_DEPENDENCIES: dict[Artifact, frozenset[str]] = {
    "destination_research": frozenset({"destination"}),
    "flight_options": frozenset({
        "origin",
        "destination",
        "start_date",
    }),
    "hotel_options": frozenset({
        "destination",
        "start_date",
        "end_date",
        "duration_days",
        "travelers",
        "budget",
        "currency",
    }),
    "activity_options": frozenset({
        "destination",
        "duration_days",
        "travelers",
        "interests",
    }),
    "itinerary": frozenset({
        "origin",
        "destination",
        "start_date",
        "duration_days",
        "travelers",
        "budget",
        "currency",
        "interests",
        "travel_style",
    }),
}

ARTIFACT_DEPENDENCIES: dict[Artifact, frozenset[Artifact]] = {
    "destination_research": frozenset(),
    "flight_options": frozenset(),
    "hotel_options": frozenset(),
    "activity_options": frozenset({"destination_research"}),
    "itinerary": frozenset({
        "destination_research",
        "flight_options",
        "hotel_options",
        "activity_options",
    }),
}


@dataclass(frozen=True)
class AppliedCorrection:
    request: TripRequest
    changed_fields: frozenset[str]


def apply_correction(
    current: TripRequest,
    correction: TripCorrection,
) -> AppliedCorrection:
    """Apply explicit edits and report the fields that truly changed."""

    values = current.model_dump()
    scalar_fields = (
        "origin",
        "destination",
        "start_date",
        "end_date",
        "start_date_text",
        "end_date_text",
        "duration_days",
        "travelers",
        "budget",
        "currency",
        "travel_style",
    )

    for field in scalar_fields:
        value = getattr(correction, field)
        if value is not None:
            values[field] = _clean_scalar(value)

    # A partial calendar correction must replace, rather than sit beside, a
    # stale complete date. Conversely, a complete date clears stale partial
    # metadata.
    if correction.start_date_text is not None:
        values["start_date"] = None
    elif correction.start_date is not None:
        values["start_date_text"] = None

    if correction.end_date_text is not None:
        values["end_date"] = None
        values["duration_days"] = None
    elif correction.end_date is not None:
        values["end_date_text"] = None

    # Duration and explicit end date are competing range representations. A
    # newly corrected duration wins by clearing the old end-date expression.
    # When both are explicitly supplied together, the explicit end date wins
    # and Python derives the inclusive duration from the two exact dates.
    if (
        correction.duration_days is not None
        and correction.duration_days != current.duration_days
        and correction.end_date is None
        and correction.end_date_text is None
    ):
        values["end_date"] = None
        values["end_date_text"] = None

    if correction.end_date is not None:
        values["duration_days"] = _inclusive_duration(
            values.get("start_date"),
            values.get("end_date"),
        )
    elif (
        correction.start_date is not None
        and values.get("end_date") is not None
    ):
        derived_duration = _inclusive_duration(
            values.get("start_date"),
            values.get("end_date"),
        )
        if derived_duration is None:
            # The new start-date representation wins over an incompatible old
            # explicit end date.
            values["end_date"] = None
            values["end_date_text"] = None
            values["duration_days"] = None
        else:
            values["duration_days"] = derived_duration

    values["interests"] = _apply_interest_operations(
        current=current.interests,
        correction=correction,
    )

    revised = TripRequest(**values)
    canonical_values = revised.model_dump()
    for field in type(current).model_fields:
        if _equivalent(
            field,
            getattr(current, field),
            getattr(revised, field),
        ):
            canonical_values[field] = getattr(current, field)
    revised = TripRequest(**canonical_values)
    changed_fields = frozenset(
        field
        for field in type(current).model_fields
        if not _equivalent(
            field,
            getattr(current, field),
            getattr(revised, field),
        )
    )
    return AppliedCorrection(
        request=revised,
        changed_fields=changed_fields,
    )


def changed_request_fields(
    before: TripRequest,
    after: TripRequest,
) -> frozenset[str]:
    """Compare two canonical requests using correction comparison rules."""

    return frozenset(
        field
        for field in type(before).model_fields
        if not _equivalent(
            field,
            getattr(before, field),
            getattr(after, field),
        )
    )


def invalidated_artifacts(
    changed_fields: set[str] | frozenset[str],
) -> tuple[Artifact, ...]:
    """Return direct and transitively dependent artifacts in safe order."""

    invalidated: set[Artifact] = {
        artifact
        for artifact, fields in DIRECT_FIELD_DEPENDENCIES.items()
        if fields.intersection(changed_fields)
    }

    changed = True
    while changed:
        changed = False
        for artifact, dependencies in ARTIFACT_DEPENDENCIES.items():
            if artifact not in invalidated and dependencies.intersection(invalidated):
                invalidated.add(artifact)
                changed = True

    return tuple(
        artifact
        for artifact in ARTIFACT_ORDER
        if artifact in invalidated
    )


def invalidate_state(
    state: TripState,
    artifacts: tuple[Artifact, ...],
) -> None:
    """Remove only invalid artifacts from the in-memory working state."""

    artifact_set = set(artifacts)
    if "destination_research" in artifact_set:
        state.destination_research = None
    if "flight_options" in artifact_set:
        state.flight_options = []
    if "hotel_options" in artifact_set:
        state.hotel_options = []
    if "activity_options" in artifact_set:
        state.activity_options = []
    if "itinerary" in artifact_set:
        state.itinerary = None


def _apply_interest_operations(
    current: list[str],
    correction: TripCorrection,
) -> list[str]:
    if (
        correction.interests_replace is None
        and not correction.interests_add
        and not correction.interests_remove
    ):
        return list(current)

    if correction.interests_replace is not None:
        interests = _unique_interests(correction.interests_replace)
    else:
        interests = _unique_interests(current)

    removed = {
        _interest_key(interest)
        for interest in correction.interests_remove
        if interest.strip()
    }
    interests = [
        interest
        for interest in interests
        if _interest_key(interest) not in removed
    ]

    known = {_interest_key(interest) for interest in interests}
    for interest in correction.interests_add:
        cleaned = " ".join(interest.split())
        key = _interest_key(cleaned)
        if cleaned and key not in known:
            interests.append(cleaned)
            known.add(key)

    return interests


def _unique_interests(interests: list[str]) -> list[str]:
    result: list[str] = []
    known: set[str] = set()
    for interest in interests:
        cleaned = " ".join(interest.split())
        key = _interest_key(cleaned)
        if cleaned and key not in known:
            result.append(cleaned)
            known.add(key)
    return result


def _interest_key(value: str) -> str:
    return " ".join(value.split()).casefold()


def _clean_scalar(value):
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def _equivalent(field: str, left, right) -> bool:
    if field == "interests":
        return [_interest_key(value) for value in left] == [
            _interest_key(value) for value in right
        ]
    if isinstance(left, str) and isinstance(right, str):
        return " ".join(left.split()).casefold() == " ".join(
            right.split()
        ).casefold()
    return left == right


def _inclusive_duration(
    start_date: str | None,
    end_date: str | None,
) -> int | None:
    if not start_date or not end_date:
        return None
    try:
        duration = (
            date.fromisoformat(end_date)
            - date.fromisoformat(start_date)
        ).days + 1
    except ValueError:
        return None
    return duration if duration > 0 else None
