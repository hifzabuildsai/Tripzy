import type {
  ActivityOption,
  CreateTripResponse,
  DestinationResearch,
  FlightOption,
  HotelOption,
  Itinerary,
  ItineraryDay,
  ItineraryItem,
  MissingRequirement,
  ResearchSource,
  TripMessageResponse,
  TripRequest,
  TripState,
  TripStateResponse,
  TripStatus,
} from "@/types/trip";

export type TripzyApiErrorCode =
  | "network"
  | "not_found"
  | "validation"
  | "unavailable"
  | "server"
  | "malformed_response";

export class TripzyApiError extends Error {
  readonly code: TripzyApiErrorCode;
  readonly status: number | null;

  constructor(
    code: TripzyApiErrorCode,
    message: string,
    status: number | null = null,
  ) {
    super(message);
    this.name = "TripzyApiError";
    this.code = code;
    this.status = status;
  }
}

type JsonObject = Record<string, unknown>;

const STATUSES = new Set<TripStatus>([
  "collecting",
  "researching_destination",
  "destination_researched",
  "researching_flights",
  "flights_researched",
  "researching_hotels",
  "hotels_researched",
  "researching_activities",
  "activities_researched",
  "planning_itinerary",
  "itinerary_planned",
]);

const MISSING_REQUIREMENTS = new Set<MissingRequirement>([
  "origin",
  "destination",
  "start_date",
  "start_date_year",
  "start_date_day",
  "end_date_or_duration",
  "travelers",
  "budget",
]);

function apiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_TRIPZY_API_URL ??
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
}

function malformed(message: string): never {
  throw new TripzyApiError(
    "malformed_response",
    `Tripzy received an unexpected server response (${message}).`,
  );
}

function object(value: unknown, field: string): JsonObject {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return malformed(`${field} is not an object`);
  }

  return value as JsonObject;
}

function string(value: unknown, field: string): string {
  if (typeof value !== "string") {
    return malformed(`${field} is not a string`);
  }

  return value;
}

function nullableString(value: unknown, field: string): string | null {
  if (value === null) {
    return null;
  }

  return string(value, field);
}

function nullableNumber(value: unknown, field: string): number | null {
  if (value === null) {
    return null;
  }

  if (typeof value !== "number" || !Number.isFinite(value)) {
    return malformed(`${field} is not a number`);
  }

  return value;
}

function number(value: unknown, field: string): number {
  const parsed = nullableNumber(value, field);

  if (parsed === null) {
    return malformed(`${field} is null`);
  }

  return parsed;
}

function list<T>(
  value: unknown,
  field: string,
  parse: (entry: unknown, field: string) => T,
): T[] {
  if (!Array.isArray(value)) {
    return malformed(`${field} is not an array`);
  }

  return value.map((entry, index) => parse(entry, `${field}[${index}]`));
}

function strings(value: unknown, field: string): string[] {
  return list(value, field, string);
}

function status(value: unknown): TripStatus {
  const parsed = string(value, "status") as TripStatus;

  if (!STATUSES.has(parsed)) {
    return malformed("status is unknown");
  }

  return parsed;
}

function missingInformation(value: unknown): MissingRequirement[] {
  return list(value, "missing_information", (entry, field) => {
    const parsed = string(entry, field) as MissingRequirement;

    if (!MISSING_REQUIREMENTS.has(parsed)) {
      return malformed(`${field} is unknown`);
    }

    return parsed;
  });
}

function source(value: unknown, field: string): ResearchSource | null {
  if (value === null) {
    return null;
  }

  const parsed = object(value, field);
  return {
    title: string(parsed.title, `${field}.title`),
    url: string(parsed.url, `${field}.url`),
  };
}

function tripRequest(value: unknown): TripRequest {
  const parsed = object(value, "state.request");
  return {
    origin: nullableString(parsed.origin, "state.request.origin"),
    destination: nullableString(parsed.destination, "state.request.destination"),
    start_date: nullableString(parsed.start_date, "state.request.start_date"),
    end_date: nullableString(parsed.end_date, "state.request.end_date"),
    start_date_text: nullableString(parsed.start_date_text, "state.request.start_date_text"),
    end_date_text: nullableString(parsed.end_date_text, "state.request.end_date_text"),
    duration_days: nullableNumber(parsed.duration_days, "state.request.duration_days"),
    travelers: nullableNumber(parsed.travelers, "state.request.travelers"),
    budget: nullableNumber(parsed.budget, "state.request.budget"),
    currency: nullableString(parsed.currency, "state.request.currency"),
    interests: strings(parsed.interests, "state.request.interests"),
    travel_style: nullableString(parsed.travel_style, "state.request.travel_style"),
  };
}

function destinationResearch(value: unknown): DestinationResearch | null {
  if (value === null) {
    return null;
  }

  const parsed = object(value, "state.destination_research");
  const namedDescriptions = (
    entries: unknown,
    field: string,
  ): { name: string; description: string }[] =>
    list(entries, field, (entry, entryField) => {
      const item = object(entry, entryField);
      return {
        name: string(item.name, `${entryField}.name`),
        description: string(item.description, `${entryField}.description`),
      };
    });

  return {
    destination: string(parsed.destination, "state.destination_research.destination"),
    attractions: namedDescriptions(parsed.attractions, "state.destination_research.attractions"),
    neighborhoods: namedDescriptions(parsed.neighborhoods, "state.destination_research.neighborhoods"),
    transportation: strings(parsed.transportation, "state.destination_research.transportation"),
    practical_tips: strings(parsed.practical_tips, "state.destination_research.practical_tips"),
    local_information: strings(parsed.local_information, "state.destination_research.local_information"),
    sources: list(parsed.sources, "state.destination_research.sources", (entry, field) => {
      const parsedSource = source(entry, field);
      if (parsedSource === null) {
        return malformed(`${field} is null`);
      }
      return parsedSource;
    }),
  };
}

function flight(value: unknown, field: string): FlightOption {
  const parsed = object(value, field);
  return {
    airline: nullableString(parsed.airline, `${field}.airline`),
    origin: string(parsed.origin, `${field}.origin`),
    destination: string(parsed.destination, `${field}.destination`),
    departure_time: nullableString(parsed.departure_time, `${field}.departure_time`),
    arrival_time: nullableString(parsed.arrival_time, `${field}.arrival_time`),
    duration: nullableString(parsed.duration, `${field}.duration`),
    stops: nullableNumber(parsed.stops, `${field}.stops`),
    price: nullableNumber(parsed.price, `${field}.price`),
    currency: nullableString(parsed.currency, `${field}.currency`),
    source: source(parsed.source, `${field}.source`),
  };
}

function hotel(value: unknown, field: string): HotelOption {
  const parsed = object(value, field);
  return {
    name: string(parsed.name, `${field}.name`),
    destination: string(parsed.destination, `${field}.destination`),
    neighborhood: nullableString(parsed.neighborhood, `${field}.neighborhood`),
    description: nullableString(parsed.description, `${field}.description`),
    price_per_night: nullableNumber(parsed.price_per_night, `${field}.price_per_night`),
    currency: nullableString(parsed.currency, `${field}.currency`),
    rating: nullableNumber(parsed.rating, `${field}.rating`),
    source: source(parsed.source, `${field}.source`),
  };
}

function activity(value: unknown, field: string): ActivityOption {
  const parsed = object(value, field);
  return {
    name: string(parsed.name, `${field}.name`),
    destination: string(parsed.destination, `${field}.destination`),
    category: nullableString(parsed.category, `${field}.category`),
    neighborhood: nullableString(parsed.neighborhood, `${field}.neighborhood`),
    description: nullableString(parsed.description, `${field}.description`),
    estimated_duration: nullableString(parsed.estimated_duration, `${field}.estimated_duration`),
    price: nullableNumber(parsed.price, `${field}.price`),
    currency: nullableString(parsed.currency, `${field}.currency`),
    source: source(parsed.source, `${field}.source`),
  };
}

function itineraryItem(value: unknown, field: string): ItineraryItem {
  const parsed = object(value, field);
  return {
    title: string(parsed.title, `${field}.title`),
    category: nullableString(parsed.category, `${field}.category`),
    start_time: nullableString(parsed.start_time, `${field}.start_time`),
    end_time: nullableString(parsed.end_time, `${field}.end_time`),
    neighborhood: nullableString(parsed.neighborhood, `${field}.neighborhood`),
    description: nullableString(parsed.description, `${field}.description`),
    estimated_duration: nullableString(parsed.estimated_duration, `${field}.estimated_duration`),
    estimated_cost: nullableNumber(parsed.estimated_cost, `${field}.estimated_cost`),
    currency: nullableString(parsed.currency, `${field}.currency`),
    notes: strings(parsed.notes, `${field}.notes`),
  };
}

function itineraryDay(value: unknown, field: string): ItineraryDay {
  const parsed = object(value, field);
  return {
    day_number: number(parsed.day_number, `${field}.day_number`),
    date: nullableString(parsed.date, `${field}.date`),
    title: nullableString(parsed.title, `${field}.title`),
    items: list(parsed.items, `${field}.items`, itineraryItem),
    notes: strings(parsed.notes, `${field}.notes`),
  };
}

function itinerary(value: unknown): Itinerary | null {
  if (value === null) {
    return null;
  }

  const parsed = object(value, "state.itinerary");
  return {
    destination: string(parsed.destination, "state.itinerary.destination"),
    start_date: string(parsed.start_date, "state.itinerary.start_date"),
    end_date: nullableString(parsed.end_date, "state.itinerary.end_date"),
    travelers: number(parsed.travelers, "state.itinerary.travelers"),
    days: list(parsed.days, "state.itinerary.days", itineraryDay),
    planning_notes: strings(parsed.planning_notes, "state.itinerary.planning_notes"),
  };
}

function tripState(value: unknown): TripState {
  const parsed = object(value, "state");
  return {
    request: tripRequest(parsed.request),
    destination_research: destinationResearch(parsed.destination_research),
    flight_options: list(parsed.flight_options, "state.flight_options", flight),
    hotel_options: list(parsed.hotel_options, "state.hotel_options", hotel),
    activity_options: list(parsed.activity_options, "state.activity_options", activity),
    itinerary: itinerary(parsed.itinerary),
    status: status(parsed.status),
  };
}

async function responseDetail(response: Response): Promise<string | null> {
  try {
    const payload = object(await response.json(), "error");
    return typeof payload.detail === "string" ? payload.detail : null;
  } catch {
    return null;
  }
}

async function request(path: string, init?: RequestInit): Promise<unknown> {
  let response: Response;

  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new TripzyApiError(
      "network",
      "Tripzy cannot reach the planning service. Check that the backend is running, then try again.",
    );
  }

  if (!response.ok) {
    const detail = await responseDetail(response);

    if (response.status === 404) {
      throw new TripzyApiError("not_found", "This trip could not be found.", 404);
    }

    if (response.status === 422) {
      throw new TripzyApiError(
        "validation",
        detail ?? "Tripzy could not understand that message. Review it and try again.",
        422,
      );
    }

    if (response.status === 503) {
      throw new TripzyApiError(
        "unavailable",
        detail ?? "Trip persistence is temporarily unavailable. Your trip has not been discarded.",
        503,
      );
    }

    throw new TripzyApiError(
      "server",
      "Tripzy hit a problem while planning this trip. Your trip is safe. Try again.",
      response.status,
    );
  }

  try {
    return await response.json();
  } catch {
    return malformed("response body is not JSON");
  }
}

export async function createTrip(): Promise<CreateTripResponse> {
  const payload = object(await request("/trips", { method: "POST" }), "create trip response");
  return {
    trip_id: string(payload.trip_id, "trip_id"),
    status: status(payload.status),
  };
}

export async function sendTripMessage(
  tripId: string,
  message: string,
): Promise<TripMessageResponse> {
  const payload = object(
    await request(`/trips/${encodeURIComponent(tripId)}/messages`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
    "message response",
  );

  const responseTripId = string(payload.trip_id, "trip_id");

  if (responseTripId !== tripId) {
    return malformed("trip_id does not match the requested trip");
  }

  return {
    trip_id: responseTripId,
    response: string(payload.response, "response"),
    status: status(payload.status),
    missing_information: missingInformation(payload.missing_information),
  };
}

export async function getTrip(tripId: string): Promise<TripStateResponse> {
  const payload = object(
    await request(`/trips/${encodeURIComponent(tripId)}`),
    "trip state response",
  );

  const responseTripId = string(payload.trip_id, "trip_id");

  if (responseTripId !== tripId) {
    return malformed("trip_id does not match the requested trip");
  }

  return {
    trip_id: responseTripId,
    state: tripState(payload.state),
    missing_information: missingInformation(payload.missing_information),
    clarification: nullableString(payload.clarification, "clarification"),
  };
}

export function userFacingApiError(error: unknown): string {
  if (error instanceof TripzyApiError) {
    return error.message;
  }

  return "Tripzy hit an unexpected problem. Please try again.";
}
