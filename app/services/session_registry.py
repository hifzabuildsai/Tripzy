from uuid import uuid4

from app.models.state import TripState
from app.services.conversation import ConversationService
from app.services.supabase_trip_repository import (
    SupabaseTripRepository,
)
from app.services.trip_repository import TripRepository


class SessionRegistry:
    """
    Coordinates Tripzy conversation sessions with
    the persistence layer.

    The registry does not own durable trip state.
    TripRepository is the source of persisted state.
    """

    def __init__(
        self,
        repository: TripRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            if repository is not None
            else SupabaseTripRepository()
        )

    def create_session(self) -> str:
        """
        Create and persist a new Tripzy planning session.
        """

        trip_id = str(uuid4())

        self.repository.create(
            trip_id=trip_id,
            state=TripState(),
        )

        return trip_id

    def get_session(
        self,
        trip_id: str,
    ) -> ConversationService | None:
        """
        Reconstruct a conversation session from
        persisted TripState.
        """

        state = self.repository.get(
            trip_id
        )

        if state is None:
            return None

        return ConversationService(
            state=state,
        )

    def save_session(
        self,
        trip_id: str,
        session: ConversationService,
    ) -> None:
        """
        Persist the latest state of a conversation session.
        """

        self.repository.save(
            trip_id=trip_id,
            state=session.get_state(),
        )

    def has_session(
        self,
        trip_id: str,
    ) -> bool:
        """
        Report whether a persisted trip exists.
        """

        return self.repository.exists(
            trip_id
        )