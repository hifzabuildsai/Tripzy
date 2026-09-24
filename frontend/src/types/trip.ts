export type TripStatus =
  | "collecting"
  | "researching_destination"
  | "destination_researched"
  | "researching_flights"
  | "flights_researched"
  | "researching_hotels"
  | "hotels_researched"
  | "researching_activities"
  | "activities_researched"
  | "planning_itinerary"
  | "itinerary_planned";

export type TripRequest = {
  origin: string | null;
  destination: string | null;
  start_date: string | null;
  end_date: string | null;
  start_date_text: string | null;
  end_date_text: string | null;
  duration_days: number | null;
  travelers: number | null;
  budget: number | null;
  currency: string | null;
  interests: string[];
  travel_style: string | null;
};

export type ResearchSource = { title: string; url: string };
export type DestinationResearch = {
  destination: string;
  attractions: { name: string; description: string }[];
  neighborhoods: { name: string; description: string }[];
  transportation: string[];
  practical_tips: string[];
  local_information: string[];
  sources: ResearchSource[];
};
export type FlightOption = {
  airline: string | null; origin: string; destination: string;
  departure_time: string | null; arrival_time: string | null;
  duration: string | null; stops: number | null; price: number | null;
  currency: string | null; source: ResearchSource | null;
};
export type HotelOption = {
  name: string; destination: string; neighborhood: string | null;
  description: string | null; price_per_night: number | null;
  currency: string | null; rating: number | null; source: ResearchSource | null;
};
export type ActivityOption = {
  name: string; destination: string; category: string | null;
  neighborhood: string | null; description: string | null;
  estimated_duration: string | null; price: number | null;
  currency: string | null; source: ResearchSource | null;
};
export type ItineraryItem = {
  title: string; category: string | null; start_time: string | null;
  end_time: string | null; neighborhood: string | null;
  description: string | null; estimated_duration: string | null;
  estimated_cost: number | null; currency: string | null; notes: string[];
};
export type ItineraryDay = {
  day_number: number; date: string | null; title: string | null;
  items: ItineraryItem[]; notes: string[];
};
export type Itinerary = {
  destination: string; start_date: string; end_date: string | null;
  travelers: number; days: ItineraryDay[]; planning_notes: string[];
};
export type TripState = {
  request: TripRequest;
  destination_research: DestinationResearch | null;
  flight_options: FlightOption[];
  hotel_options: HotelOption[];
  activity_options: ActivityOption[];
  itinerary: Itinerary | null;
  status: TripStatus;
};
export type MissingRequirement =
  | "origin" | "destination" | "start_date" | "start_date_year"
  | "start_date_day"
  | "end_date_or_duration" | "travelers" | "budget";
export type WorkspaceSection = "brief" | "research" | "options" | "itinerary";

export type CreateTripResponse = {
  trip_id: string;
  status: TripStatus;
};

export type TripMessageResponse = {
  trip_id: string;
  response: string;
  status: TripStatus;
  missing_information: MissingRequirement[];
};

export type TripStateResponse = {
  trip_id: string;
  state: TripState;
  missing_information: MissingRequirement[];
  clarification: string | null;
};
