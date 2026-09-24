import type { TripStatus, WorkspaceSection } from "@/types/trip";

export type ExecutionStepState = "waiting" | "active" | "complete";
export type ExecutionStep = { id: string; label: string; state: ExecutionStepState };

const STATUS_ORDER: TripStatus[] = [
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
];

export function mapStatusToExecution(status: TripStatus): ExecutionStep[] {
  const current = STATUS_ORDER.indexOf(status);
  const steps = [
    { id: "understood", label: "Trip understood", start: 0, done: 1 },
    { id: "destination", label: "Destination research", start: 1, done: 2 },
    { id: "flights", label: "Flights", start: 3, done: 4 },
    { id: "stays", label: "Stays", start: 5, done: 6 },
    { id: "activities", label: "Activities", start: 7, done: 8 },
    { id: "itinerary", label: "Itinerary", start: 9, done: 10 },
  ];

  return steps.map(({ id, label, start, done }) => ({
    id,
    label,
    state: current >= done ? "complete" : current >= start ? "active" : "waiting",
  }));
}

export function normalizeWorkspaceSection(value: string | undefined): WorkspaceSection {
  if (value === "discover" || value === "research") {
    return "research";
  }

  if (value === "options" || value === "itinerary") {
    return value;
  }

  return "brief";
}

export function workspaceSectionQuery(section: WorkspaceSection): string {
  return section === "research" ? "discover" : section;
}
