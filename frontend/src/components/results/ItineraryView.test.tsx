import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import ItineraryView from "@/components/results/ItineraryView";
import type { Itinerary } from "@/types/trip";

describe("itinerary currency rendering", () => {
  it("renders a persisted Turkish-lira alias without crashing the workspace", () => {
    const itinerary: Itinerary = {
      destination: "Istanbul",
      start_date: "2027-09-01",
      end_date: "2027-09-05",
      travelers: 2,
      planning_notes: [],
      days: [
        {
          day_number: 1,
          date: "2027-09-01",
          title: "History day",
          notes: [],
          items: [
            {
              title: "Istanbul Archaeology Museums",
              category: "museum",
              start_time: "15:30",
              end_time: "17:00",
              neighborhood: "Sultanahmet",
              description: "Museum visit.",
              estimated_duration: "90 minutes",
              estimated_cost: 600,
              currency: "TL",
              notes: ["Matches the history interest."],
            },
          ],
        },
      ],
    };

    const html = renderToStaticMarkup(<ItineraryView itinerary={itinerary} />);

    expect(html).toContain("Istanbul Archaeology Museums");
    expect(html).toContain("600");
  });
});
