import os

from dotenv import load_dotenv
from supabase import Client, create_client

from app.models.state import TripState
from app.services.trip_repository import (
    TripRepository,
    TripRepositoryError,
)


load_dotenv()


class SupabaseTripRepository(TripRepository):
    """
    Supabase PostgreSQL implementation of TripRepository.

    TripState is persisted as a JSONB document in the
    public.trips table.
    """

    def __init__(
        self,
        client: Client | None = None,
    ) -> None:
        if client is not None:
            self.client = client
            return

        supabase_url = os.getenv(
            "SUPABASE_URL"
        )
        supabase_key = os.getenv(
            "SUPABASE_KEY"
        )

        if not supabase_url:
            raise ValueError(
                "SUPABASE_URL is not set."
            )

        if not supabase_key:
            raise ValueError(
                "SUPABASE_KEY is not set."
            )

        try:
            self.client = create_client(
                supabase_url,
                supabase_key,
            )
        except Exception as exc:
            raise TripRepositoryError(
                "Failed to initialize Supabase persistence."
            ) from exc

    def create(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        """
        Persist a newly created trip.
        """

        try:
            self.client.table(
                "trips"
            ).insert(
                {
                    "id": trip_id,
                    "state": state.model_dump(
                        mode="json"
                    ),
                }
            ).execute()
        except Exception as exc:
            raise TripRepositoryError(
                "Failed to create trip."
            ) from exc

    def get(
        self,
        trip_id: str,
    ) -> TripState | None:
        """
        Load and validate persisted TripState.
        """

        try:
            response = (
                self.client.table("trips")
                .select("state")
                .eq("id", trip_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise TripRepositoryError(
                "Failed to load trip."
            ) from exc

        if not response.data:
            return None

        return TripState.model_validate(
            response.data[0]["state"]
        )

    def save(
        self,
        trip_id: str,
        state: TripState,
    ) -> None:
        """
        Persist the latest TripState.
        """

        try:
            self.client.table(
                "trips"
            ).update(
                {
                    "state": state.model_dump(
                        mode="json"
                    ),
                }
            ).eq(
                "id",
                trip_id,
            ).execute()
        except Exception as exc:
            raise TripRepositoryError(
                "Failed to save trip."
            ) from exc

    def exists(
        self,
        trip_id: str,
    ) -> bool:
        """
        Report whether the trip exists.
        """

        try:
            response = (
                self.client.table("trips")
                .select("id")
                .eq("id", trip_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise TripRepositoryError(
                "Failed to check trip existence."
            ) from exc

        return bool(response.data)