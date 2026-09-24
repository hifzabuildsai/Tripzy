import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import DestinationResearchView from "@/components/results/DestinationResearchView";
import ItineraryView from "@/components/results/ItineraryView";
import { buildPreviewState } from "@/data/demo-trip";
import { applyMissionMessage, buildClarification, EMPTY_TRIP_REQUEST, getMissingRequirements, mapStatusToExecution } from "@/lib/mission-intake";

const RICH_MISSION = "I want to travel from Karachi to Seoul around April 2027 for 6 days with my sister. Budget around $2,500. We love food, culture, shopping and cafés, and we don’t want a rushed itinerary.";

describe("mission intake", () => {
  it("renders a rich mission as structured application state", () => {
    const request = applyMissionMessage(EMPTY_TRIP_REQUEST, RICH_MISSION);
    expect(request).toMatchObject({
      origin: "Karachi", destination: "Seoul", start_date_text: "April 2027",
      duration_days: 6, travelers: 2, budget: 2500, currency: "USD",
      travel_style: "Relaxed pace",
    });
    expect(request.interests).toEqual(["food", "culture", "shopping", "cafés"]);
    expect(getMissingRequirements(request)).toEqual([]);
  });

  it("preserves unaffected constraints during a natural correction", () => {
    const original = applyMissionMessage(EMPTY_TRIP_REQUEST, RICH_MISSION);
    const revised = applyMissionMessage(original, "Actually make it Istanbul, same dates, raise the budget to $3,000, and focus more on history.");
    expect(revised.destination).toBe("Istanbul");
    expect(revised.budget).toBe(3000);
    expect(revised.start_date_text).toBe("April 2027");
    expect(revised.travelers).toBe(2);
    expect(revised.interests).toEqual(["food", "culture", "shopping", "cafés", "history"]);
  });

  it("asks once for every missing critical field", () => {
    const partial = applyMissionMessage(EMPTY_TRIP_REQUEST, "Seoul for 6 days, food and culture");
    const clarification = buildClarification(partial);
    expect(clarification).toContain("departure city");
    expect(clarification).toContain("travel dates");
    expect(clarification).toContain("number of travelers");
    expect(clarification).toContain("approximate budget");
    expect(clarification).toContain("one message");
  });

  it("maps backend status to honest execution presentation", () => {
    const flightStage = mapStatusToExecution("researching_flights");
    expect(flightStage.find((step) => step.id === "destination")?.state).toBe("complete");
    expect(flightStage.find((step) => step.id === "flights")?.state).toBe("active");
    expect(flightStage.find((step) => step.id === "stays")?.state).toBe("waiting");
  });
});

describe("backend-shaped result artifacts", () => {
  const request = applyMissionMessage(EMPTY_TRIP_REQUEST, RICH_MISSION);
  const state = buildPreviewState(request);

  it("switches all destination artifacts when the mission changes", () => {
    const revised = applyMissionMessage(request, "Actually make it Istanbul, same dates.");
    const next = buildPreviewState(revised);
    expect(next.destination_research?.destination).toBe("Istanbul");
    expect(next.itinerary?.destination).toBe("Istanbul");
    expect(next.hotel_options.every((hotel) => hotel.destination === "Istanbul")).toBe(true);
  });

  it("renders destination research from the real schema", () => {
    const html = renderToStaticMarkup(<DestinationResearchView research={state.destination_research!} />);
    expect(html).toContain("Where to base yourself");
    expect(html).toContain("Gyeongbokgung Palace");
    expect(html).toContain("Research sources");
  });

  it("renders a complete day-by-day itinerary", () => {
    const html = renderToStaticMarkup(<ItineraryView itinerary={state.itinerary!} />);
    expect(html).toContain("Seoul, day by day");
    expect(html).toContain("Day 1");
    expect(html).toContain("Day 6");
    expect(html).toContain("Planning notes");
  });
});
