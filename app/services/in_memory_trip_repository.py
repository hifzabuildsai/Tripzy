from copy import deepcopy

from app.models.state import TripState
from app.services.trip_repository import TripRepository


class InMemoryTripRepository(TripRepository):
    """
    In-memory implementation of the TripRepository contract.

    Used for local development and deterministic tests.
    Data is process-local and is not durable.
    """

    def __init__(self) -> None:
        self._trips: dict[str, TripState] = {}

    def create(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        self._trips[trip_id] = deepcopy(state)

    def get(
        self,
        trip_id: str,
    ) -> TripState | None:
        state = self._trips.get(trip_id)

        if state is None:
            return None

        return deepcopy(state)

    def save(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        self._trips[trip_id] = deepcopy(state)

    def exists(
        self,
        trip_id: str,
    ) -> bool:
        return trip_id in self._trips