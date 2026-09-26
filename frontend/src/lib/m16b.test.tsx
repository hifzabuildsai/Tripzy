import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import TripRevisionPanel from "@/components/tripzy/TripRevisionPanel";
import { IntakePrompt, PlanningPending } from "@/components/tripzy/WorkspaceStates";
import { getTrip, sendTripMessage } from "@/lib/tripzy-api";
import type { TripStateResponse } from "@/types/trip";

const TRIP_ID = "same-trip-id";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function canonicalTrip(duration = 8): TripStateResponse {
  return {
    trip_id: TRIP_ID,
    missing_information: [],
    clarification: null,
    state: {
      request: {
        origin: "Karachi",
        destination: "Seoul",
        start_date: "2027-09-10",
        end_date: null,
        start_date_text: null,
        end_date_text: null,
        duration_days: duration,
        travelers: 2,
        budget: 2000,
        currency: "USD",
        interests: ["food", "museums"],
        travel_style: "relaxed",
      },
      destination_research: null,
      flight_options: [],
      hotel_options: [],
      activity_options: [],
      itinerary: {
        destination: "Seoul",
        start_date: "2027-09-10",
        end_date: "2027-09-17",
        travelers: 2,
        days: [],
        planning_notes: [],
      },
      status: "itinerary_planned",
    },
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("M16B revision experience", () => {
  it("exposes a calm Change the plan action and natural correction composer", () => {
    const closed = renderToStaticMarkup(
      <TripRevisionPanel
        open={false}
        error={null}
        failedMessage={null}
        onOpen={() => undefined}
        onSubmit={async () => true}
        onRetry={() => undefined}
      />,
    );
    const open = renderToStaticMarkup(
      <TripRevisionPanel
        open
        error={null}
        failedMessage={null}
        onOpen={() => undefined}
        onSubmit={async () => true}
        onRetry={() => undefined}
      />,
    );

    expect(closed).toContain("Change the plan");
    expect(open).toContain("Describe the trip correction");
    expect(open).toContain("Make it 8 days, remove shopping and add museums");
    expect(open).not.toContain("chat");
  });

  it("uses truthful revision-pending copy without fake stages or percentages", () => {
    const html = renderToStaticMarkup(<PlanningPending updating />);
    expect(html).toContain("Tripzy is updating your trip");
    expect(html).toContain("saved plan remains available");
    expect(html).not.toContain("Researching flights");
    expect(html).not.toMatch(/\d+%/);
  });

  it("posts the correction and fetches canonical state using only the same trip id", async () => {
    const correction = "Make it 8 days and add museums.";
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({
        trip_id: TRIP_ID,
        response: "Revised itinerary ready.",
        status: "itinerary_planned",
        missing_information: [],
      }))
      .mockResolvedValueOnce(jsonResponse(canonicalTrip()));
    vi.stubGlobal("fetch", fetchMock);

    await sendTripMessage(TRIP_ID, correction);
    const result = await getTrip(TRIP_ID);

    expect(result.state.request.duration_days).toBe(8);
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      `http://127.0.0.1:8000/trips/${TRIP_ID}/messages`,
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ message: correction }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      `http://127.0.0.1:8000/trips/${TRIP_ID}`,
      expect.objectContaining({ cache: "no-store" }),
    );
    expect(fetchMock.mock.calls.some(([url]) => (
      url === "http://127.0.0.1:8000/trips"
    ))).toBe(false);
  });

  it("keeps the exact failed correction for a safe same-trip retry", async () => {
    const correction = "Reduce the budget to $2,000.";
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ detail: "failed" }, 500))
      .mockResolvedValueOnce(jsonResponse({
        trip_id: TRIP_ID,
        response: "Revised itinerary ready.",
        status: "itinerary_planned",
        missing_information: [],
      }))
      .mockResolvedValueOnce(jsonResponse(canonicalTrip()));
    vi.stubGlobal("fetch", fetchMock);

    await expect(sendTripMessage(TRIP_ID, correction)).rejects.toMatchObject({
      code: "server",
      status: 500,
    });
    await sendTripMessage(TRIP_ID, correction);
    await getTrip(TRIP_ID);

    const messageCalls = fetchMock.mock.calls.filter(([url]) => (
      url === `http://127.0.0.1:8000/trips/${TRIP_ID}/messages`
    ));
    expect(messageCalls).toHaveLength(2);
    expect(messageCalls[0][1]).toEqual(expect.objectContaining({
      body: JSON.stringify({ message: correction }),
    }));
    expect(messageCalls[1][1]).toEqual(expect.objectContaining({
      body: JSON.stringify({ message: correction }),
    }));
  });

  it("returns a partial-date revision to backend-owned clarification on the same route", async () => {
    const partial = canonicalTrip();
    partial.missing_information = ["start_date_day"];
    partial.clarification = "To plan your trip, please share: the day of the month for your travel start date.";
    partial.state.request.start_date = null;
    partial.state.request.start_date_text = "October 2028";
    partial.state.itinerary = null;
    partial.state.status = "collecting";
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({
        trip_id: TRIP_ID,
        response: partial.clarification,
        status: "collecting",
        missing_information: ["start_date_day"],
      }))
      .mockResolvedValueOnce(jsonResponse(partial));
    vi.stubGlobal("fetch", fetchMock);

    await sendTripMessage(TRIP_ID, "Move it to October 2028.");
    const restored = await getTrip(TRIP_ID);
    const html = renderToStaticMarkup(
      <IntakePrompt pristine={false} prompt={restored.clarification!} />,
    );

    expect(restored.trip_id).toBe(TRIP_ID);
    expect(restored.missing_information).toEqual(["start_date_day"]);
    expect(restored.state.request.start_date).toBeNull();
    expect(restored.state.request.start_date_text).toBe("October 2028");
    expect(html).toContain("day of the month");
  });

  it("renders the preserved correction and retry action after failure", () => {
    const correction = "Actually change Seoul to Istanbul.";
    const html = renderToStaticMarkup(
      <TripRevisionPanel
        open={false}
        error="Your trip is safe. Try again."
        failedMessage={correction}
        onOpen={() => undefined}
        onSubmit={async () => true}
        onRetry={() => undefined}
      />,
    );

    expect(html).toContain(correction);
    expect(html).toContain("Retry this change");
    expect(html).toContain("Your trip is safe");
  });
});
