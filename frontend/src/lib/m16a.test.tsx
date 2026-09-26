import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import DestinationResearchView from "@/components/results/DestinationResearchView";
import ItineraryView from "@/components/results/ItineraryView";
import TravelOptionsView from "@/components/results/TravelOptionsView";
import TripBrief from "@/components/tripzy/TripBrief";
import WorkspaceNav from "@/components/tripzy/WorkspaceNav";
import {
  IntakePrompt,
  PlanningPending,
  TripNotFound,
} from "@/components/tripzy/WorkspaceStates";
import {
  clearPendingMission,
  createTripForMission,
  getPendingMission,
} from "@/lib/mission-handoff";
import {
  normalizeWorkspaceSection,
  workspaceSectionQuery,
} from "@/lib/trip-status";
import { resolveStickerWorld } from "@/data/stickers/registry";
import {
  getTrip,
  sendTripMessage,
  TripzyApiError,
} from "@/lib/tripzy-api";
import type { TripStateResponse } from "@/types/trip";

const TRIP_ID = "d9dbe35a-5bfd-4de6-871d-541fd066e096";

const RESTORED_TRIP: TripStateResponse = {
  trip_id: TRIP_ID,
  missing_information: [],
  clarification: null,
  state: {
    request: {
      origin: "Karachi",
      destination: "Lisbon",
      start_date: "2027-09-10",
      end_date: null,
      start_date_text: null,
      end_date_text: null,
      duration_days: 3,
      travelers: 2,
      budget: 2000,
      currency: "USD",
      interests: ["food", "history"],
      travel_style: "relaxed",
    },
    destination_research: {
      destination: "Lisbon",
      attractions: [{ name: "Jerónimos Monastery", description: "A researched historic site." }],
      neighborhoods: [{ name: "Alfama", description: "A historic hillside neighborhood." }],
      transportation: ["Use the metro for longer cross-city trips."],
      practical_tips: ["Wear comfortable shoes."],
      local_information: ["Hills shape walking routes."],
      sources: [{ title: "Visit Lisboa", url: "https://www.visitlisboa.com/" }],
    },
    flight_options: [{
      airline: "Research Air",
      origin: "Karachi",
      destination: "Lisbon",
      departure_time: null,
      arrival_time: null,
      duration: "14h",
      stops: 1,
      price: 850,
      currency: "USD",
      source: null,
    }],
    hotel_options: [{
      name: "Lisbon Research Hotel",
      destination: "Lisbon",
      neighborhood: "Alfama",
      description: "A researched accommodation candidate.",
      price_per_night: 120,
      currency: "USD",
      rating: 4.4,
      source: null,
    }],
    activity_options: [{
      name: "Jerónimos Monastery",
      destination: "Lisbon",
      category: "History",
      neighborhood: "Belém",
      description: "A researched visit.",
      estimated_duration: "2 hours",
      price: null,
      currency: null,
      source: null,
    }],
    itinerary: {
      destination: "Lisbon",
      start_date: "2027-09-10",
      end_date: "2027-09-12",
      travelers: 2,
      days: [{
        day_number: 1,
        date: "2027-09-10",
        title: "Historic Lisbon",
        items: [{
          title: "Jerónimos Monastery",
          category: "History",
          start_time: "10:00",
          end_time: "12:00",
          neighborhood: "Belém",
          description: "A paced historic visit.",
          estimated_duration: "2 hours",
          estimated_cost: null,
          currency: null,
          notes: [],
        }],
        notes: [],
      }],
      planning_notes: ["Research candidates require availability checks."],
    },
    status: "itinerary_planned",
  },
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  clearPendingMission(TRIP_ID);
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("M16A mission handoff and API boundary", () => {
  it("creates a real trip, preserves the untouched mission, and sends it to the same trip id", async () => {
    const mission = "  Plan a calm food trip from Karachi to Lisbon\nfor two people.  ";
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ trip_id: TRIP_ID, status: "collecting" }, 201))
      .mockResolvedValueOnce(jsonResponse({
        trip_id: TRIP_ID,
        response: "Please share your dates and approximate budget in one message.",
        status: "collecting",
        missing_information: ["start_date", "budget"],
      }));
    vi.stubGlobal("fetch", fetchMock);

    const tripId = await createTripForMission(mission);
    const pendingMission = getPendingMission(TRIP_ID);
    expect(tripId).toBe(TRIP_ID);
    expect(pendingMission).toBe(mission);

    await sendTripMessage(tripId, pendingMission!);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "http://127.0.0.1:8000/trips",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      `http://127.0.0.1:8000/trips/${TRIP_ID}/messages`,
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ message: mission }),
      }),
    );
  });

  it("restores the persisted TripState through the durable route API", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(RESTORED_TRIP));
    vi.stubGlobal("fetch", fetchMock);

    const restored = await getTrip(TRIP_ID);

    expect(restored).toEqual(RESTORED_TRIP);
    expect(fetchMock).toHaveBeenCalledWith(
      `http://127.0.0.1:8000/trips/${TRIP_ID}`,
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("accepts backend day-missing metadata for a preserved month and year", async () => {
    const monthYearTrip: TripStateResponse = {
      ...RESTORED_TRIP,
      missing_information: ["start_date_day"],
      clarification: "To plan your trip, please share: the day of the month for your travel start date.",
      state: {
        ...RESTORED_TRIP.state,
        request: {
          ...RESTORED_TRIP.state.request,
          start_date: null,
          start_date_text: "September 2027",
        },
      },
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(monthYearTrip)));

    const restored = await getTrip(TRIP_ID);

    expect(restored.missing_information).toEqual(["start_date_day"]);
    expect(restored.state.request.start_date_text).toBe("September 2027");
  });

  it("sends a consolidated clarification reply to the existing trip", async () => {
    const reply = "Karachi, September 10 2027, two people, around $2,000.";
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      trip_id: TRIP_ID,
      response: "Your itinerary is ready.",
      status: "itinerary_planned",
      missing_information: [],
    }));
    vi.stubGlobal("fetch", fetchMock);

    await sendTripMessage(TRIP_ID, reply);

    expect(fetchMock).toHaveBeenCalledWith(
      `http://127.0.0.1:8000/trips/${TRIP_ID}/messages`,
      expect.objectContaining({ body: JSON.stringify({ message: reply }) }),
    );
  });

  it("keeps the mission and real trip identity available after an ambiguous network failure", async () => {
    const mission = "Karachi to Lisbon, September 2027, two travelers.";
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ trip_id: TRIP_ID, status: "collecting" }, 201))
      .mockRejectedValueOnce(new Error("connection lost"));
    vi.stubGlobal("fetch", fetchMock);

    const tripId = await createTripForMission(mission);
    await expect(sendTripMessage(tripId, mission)).rejects.toMatchObject({
      code: "network",
      message: expect.stringContaining("cannot reach the planning service"),
    });
    expect(tripId).toBe(TRIP_ID);
    expect(getPendingMission(TRIP_ID)).toBe(mission);
  });

  it("retries an HTTP 500 with the same trip id and untouched message", async () => {
    const reply = "Start on September 10.";
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ detail: "Internal failure" }, 500))
      .mockResolvedValueOnce(jsonResponse({
        trip_id: TRIP_ID,
        response: "Your itinerary is ready.",
        status: "itinerary_planned",
        missing_information: [],
      }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(sendTripMessage(TRIP_ID, reply)).rejects.toMatchObject({
      code: "server",
      status: 500,
    });
    await sendTripMessage(TRIP_ID, reply);

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      `http://127.0.0.1:8000/trips/${TRIP_ID}/messages`,
      expect.objectContaining({ body: JSON.stringify({ message: reply }) }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      `http://127.0.0.1:8000/trips/${TRIP_ID}/messages`,
      expect.objectContaining({ body: JSON.stringify({ message: reply }) }),
    );
  });

  it.each([
    [404, "not_found"],
    [422, "validation"],
    [503, "unavailable"],
  ])("maps HTTP %s to a useful typed error", async (status, code) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ detail: "Safe detail" }, status)));
    const error = await getTrip(TRIP_ID).catch((caught) => caught);
    expect(error).toBeInstanceOf(TripzyApiError);
    expect(error).toMatchObject({ code, status });
  });

  it("rejects malformed responses instead of inventing frontend state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ trip_id: TRIP_ID, state: {} })));
    await expect(getTrip(TRIP_ID)).rejects.toMatchObject({ code: "malformed_response" });
  });

  it("rejects a response whose trip id does not match the durable route", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      ...RESTORED_TRIP,
      trip_id: "another-trip-id",
    })));

    await expect(getTrip(TRIP_ID)).rejects.toMatchObject({ code: "malformed_response" });
  });

  it("does not expose unexpected backend error detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      detail: "Traceback: secret-token-value",
    }, 500)));

    const error = await getTrip(TRIP_ID).catch((caught) => caught);

    expect(error).toMatchObject({ code: "server", status: 500 });
    expect(error.message).toBe(
      "Tripzy hit a problem while planning this trip. Your trip is safe. Try again.",
    );
    expect(error.message).not.toContain("cannot reach");
    expect(error.message).not.toContain("Traceback");
    expect(error.message).not.toContain("secret-token-value");
  });
});

describe("M16A real-state presentation", () => {
  it("renders the backend clarification verbatim", () => {
    const clarification = "Tell me your departure city, dates, travelers and approximate budget. You can give me everything in one message.";
    const html = renderToStaticMarkup(<IntakePrompt pristine={false} prompt={clarification} />);
    expect(html).toContain("One clarification");
    expect(html).toContain("departure city, dates, travelers and approximate budget");
  });

  it("renders real TripState artifacts without substituting Seoul preview data", () => {
    const state = RESTORED_TRIP.state;
    const html = [
      renderToStaticMarkup(<TripBrief request={state.request} />),
      renderToStaticMarkup(<DestinationResearchView research={state.destination_research!} />),
      renderToStaticMarkup(<TravelOptionsView flights={state.flight_options} hotels={state.hotel_options} />),
      renderToStaticMarkup(<ItineraryView itinerary={state.itinerary!} />),
    ].join("\n");

    expect(html).toContain("Karachi");
    expect(html).toContain("Lisbon");
    expect(html).toContain("Alfama");
    expect(html).toContain("Lisbon Research Hotel");
    expect(html).toContain("Historic Lisbon");
    expect(html).not.toContain("Seoul");
    expect(html).not.toContain("Gyeongbokgung");
    expect(resolveStickerWorld("Lisbon").id).toBe("universal");
  });

  it("uses one truthful pending state with no fake stages or percentages", () => {
    const html = renderToStaticMarkup(<PlanningPending />);
    expect(html).toContain("Tripzy is planning your trip");
    expect(html).not.toContain("Researching flights");
    expect(html).not.toMatch(/\d+%/);
  });

  it("renders a safe trip-not-found state with a new-trip action", () => {
    const html = renderToStaticMarkup(<TripNotFound />);
    expect(html).toContain("Trip not found");
    expect(html).toContain("Start a new trip");
    expect(html).toContain('href="/"');
  });
});

describe("M16A durable workspace navigation", () => {
  it("normalizes URL view state and preserves discover naming", () => {
    expect(normalizeWorkspaceSection(undefined)).toBe("brief");
    expect(normalizeWorkspaceSection("discover")).toBe("research");
    expect(normalizeWorkspaceSection("options")).toBe("options");
    expect(normalizeWorkspaceSection("itinerary")).toBe("itinerary");
    expect(normalizeWorkspaceSection("unknown")).toBe("brief");
    expect(workspaceSectionQuery("research")).toBe("discover");
  });

  it("renders history-aware links for every workspace view", () => {
    const html = renderToStaticMarkup(<WorkspaceNav active="brief" tripId={TRIP_ID} />);
    expect(html).toContain(`/trips/${TRIP_ID}?view=brief`);
    expect(html).toContain(`/trips/${TRIP_ID}?view=discover`);
    expect(html).toContain(`/trips/${TRIP_ID}?view=options`);
    expect(html).toContain(`/trips/${TRIP_ID}?view=itinerary`);
  });
});
