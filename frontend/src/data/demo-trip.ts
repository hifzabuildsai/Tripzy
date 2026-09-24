import type { ActivityOption, FlightOption, HotelOption, ItineraryDay, TripRequest, TripState } from "@/types/trip";

const DESTINATIONS = {
  seoul: {
    name: "Seoul",
    neighborhoods: [
      ["Seochon", "A low-rise base near Gyeongbokgung with galleries, cafés and easy access to historic Seoul."],
      ["Euljiro", "Central, well connected and full of workshops, coffee bars and late-night food."],
      ["Hannam", "A calmer design-led area with independent shops and access to the river."],
    ],
    attractions: [
      ["Gyeongbokgung Palace", "A strong first-day anchor for royal history and traditional architecture."],
      ["Gwangjang Market", "A compact food stop for mung-bean pancakes, noodles and market culture."],
      ["Leeum Museum", "A thoughtful bridge between Korean heritage and contemporary art."],
    ],
    transit: ["T-money works across metro and buses.", "Airport Railroad connects Incheon with central Seoul."],
    tips: ["Keep one flexible evening for weather-dependent city views.", "Many independent cafés open later in the morning."],
    local: ["Build food stops around neighborhoods to avoid cross-city backtracking.", "Palace areas pair naturally with Seochon and Bukchon."],
    source: { title: "Visit Seoul", url: "https://english.visitseoul.net/" },
  },
  istanbul: {
    name: "Istanbul",
    neighborhoods: [
      ["Karaköy", "A walkable waterfront base between historic sights, ferries and modern cafés."],
      ["Kadıköy", "A lively Asian-side base for markets, food and a more local evening rhythm."],
      ["Sultanahmet", "Best for early access to major historic monuments, with a quieter night scene."],
    ],
    attractions: [
      ["Hagia Sophia", "A defining historic landmark that rewards an early, uncrowded visit."],
      ["Bosphorus ferry", "A practical crossing and one of the clearest ways to understand the city."],
      ["Spice Bazaar", "A compact sensory stop that fits well into an Eminönü food walk."],
    ],
    transit: ["Istanbulkart covers ferries, metro, trams and buses.", "Ferries can be both transport and a scenic break."],
    tips: ["Group old-city sights together and start early.", "Leave buffer time around bridge and cross-city transfers."],
    local: ["The European and Asian sides have distinct daily rhythms.", "Food-focused planning works best market by market."],
    source: { title: "GoTürkiye", url: "https://goturkiye.com/" },
  },
} as const;

function destinationData(destination: string | null) {
  return destination?.toLowerCase().includes("istanbul") ? DESTINATIONS.istanbul : DESTINATIONS.seoul;
}

function flightOptions(request: TripRequest): FlightOption[] {
  const origin = request.origin ?? "Departure city";
  const destination = request.destination ?? "Destination";
  return [
    { airline: "Best balanced route", origin, destination, departure_time: "09:15", arrival_time: "22:40", duration: "13h 25m", stops: 1, price: 780, currency: "USD", source: null },
    { airline: "Shortest researched route", origin, destination, departure_time: "03:30", arrival_time: "15:20", duration: "11h 50m", stops: 1, price: 925, currency: "USD", source: null },
  ];
}

function hotelOptions(request: TripRequest): HotelOption[] {
  const data = destinationData(request.destination);
  return data.neighborhoods.slice(0, 2).map(([neighborhood, description], index) => ({
    name: index === 0 ? `${neighborhood} House` : `${neighborhood} Stay`,
    destination: data.name, neighborhood, description,
    price_per_night: index === 0 ? 128 : 96, currency: "USD",
    rating: index === 0 ? 4.7 : 4.5, source: null,
  }));
}

function activityOptions(request: TripRequest): ActivityOption[] {
  const data = destinationData(request.destination);
  return data.attractions.map(([name, description], index) => ({
    name, destination: data.name,
    category: index === 1 ? "Food & local life" : "Culture",
    neighborhood: data.neighborhoods[index]?.[0] ?? null,
    description, estimated_duration: index === 1 ? "2 hours" : "2–3 hours",
    price: index === 1 ? 25 : 18, currency: "USD", source: data.source,
  }));
}

function itineraryDays(request: TripRequest): ItineraryDay[] {
  const data = destinationData(request.destination);
  const count = Math.min(request.duration_days ?? 3, 6);
  const themes = data.name === "Istanbul"
    ? ["Old city, slowly", "Markets and the Golden Horn", "Across the Bosphorus", "Local food trail", "Design and waterfront", "A flexible farewell"]
    : ["Palaces and old Seoul", "Market flavors", "Design and contemporary Seoul", "Neighborhood café day", "River and city views", "A flexible farewell"];
  return Array.from({ length: count }, (_, index) => {
    const attraction = data.attractions[index % data.attractions.length];
    const neighborhood = data.neighborhoods[index % data.neighborhoods.length];
    return {
      day_number: index + 1, date: null, title: themes[index],
      items: [
        { title: attraction[0], category: "Anchor", start_time: "09:30", end_time: "12:00", neighborhood: neighborhood[0], description: attraction[1], estimated_duration: "2–3 hours", estimated_cost: 18, currency: "USD", notes: ["Start before the busiest period."] },
        { title: `${neighborhood[0]} at your own pace`, category: "Explore", start_time: "14:00", end_time: "17:30", neighborhood: neighborhood[0], description: neighborhood[1], estimated_duration: "3 hours", estimated_cost: 35, currency: "USD", notes: ["Keep room for an unplanned café or shop."] },
      ],
      notes: index === count - 1 ? ["Keep the final evening flexible."] : [],
    };
  });
}

export function buildPreviewState(request: TripRequest): TripState {
  const data = destinationData(request.destination);
  return {
    request,
    destination_research: {
      destination: data.name,
      attractions: data.attractions.map(([name, description]) => ({ name, description })),
      neighborhoods: data.neighborhoods.map(([name, description]) => ({ name, description })),
      transportation: [...data.transit], practical_tips: [...data.tips],
      local_information: [...data.local], sources: [data.source],
    },
    flight_options: flightOptions(request), hotel_options: hotelOptions(request),
    activity_options: activityOptions(request),
    itinerary: {
      destination: data.name,
      start_date: request.start_date ?? request.start_date_text ?? "Date to confirm",
      end_date: request.end_date,
      travelers: request.travelers ?? 1,
      days: itineraryDays(request),
      planning_notes: ["Options are research candidates and require availability checks before booking.", `Built for a ${request.travel_style?.toLowerCase() ?? "balanced"} trip.`],
    },
    status: "itinerary_planned",
  };
}
