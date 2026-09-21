from abc import ABC, abstractmethod

from app.models.state import TripState


class TripRepositoryError(Exception):
    """
    Raised when the trip persistence layer cannot
    complete a repository operation.
    """


class TripRepository(ABC):
    """
    Persistence boundary for Tripzy trip state.

    Application code depends on this contract rather than
    depending directly on a specific database provider.
    """

    @abstractmethod
    def create(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        """
        Persist a newly created trip.
        """
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        trip_id: str,
    ) -> TripState | None:
        """
        Return the persisted state for a trip.
        """
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        """
        Persist the latest state of an existing trip.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(
        self,
        trip_id: str,
    ) -> bool:
        """
        Report whether a persisted trip exists.
        """
        raise NotImplementedError