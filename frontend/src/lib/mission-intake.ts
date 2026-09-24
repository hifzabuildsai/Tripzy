import type { MissingRequirement, TripRequest, TripStatus } from "@/types/trip";

export const EMPTY_TRIP_REQUEST: TripRequest = {
  origin: null, destination: null, start_date: null, end_date: null,
  start_date_text: null, end_date_text: null, duration_days: null,
  travelers: null, budget: null, currency: "USD", interests: [], travel_style: null,
};

const MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
const INTERESTS = ["food", "culture", "shopping", "cafés", "cafes", "history", "architecture", "nature", "museums", "nightlife", "photography"];
const NUMBER_WORDS: Record<string, number> = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6 };

function titleCase(value: string): string {
  return value.trim().replace(/\s+/g, " ").split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(" ");
}

function parseMoney(message: string): Pick<TripRequest, "budget" | "currency"> | null {
  const match = message.match(/(?:\$|usd\s*)\s*([0-9][0-9,]*(?:\.\d{1,2})?)|([0-9][0-9,]*(?:\.\d{1,2})?)\s*(usd|dollars?|pkr|eur|gbp)/i);
  if (!match) return null;
  const amount = Number((match[1] ?? match[2]).replaceAll(",", ""));
  const token = (match[3] ?? "USD").toUpperCase();
  const currency = token.startsWith("DOLLAR") ? "USD" : token;
  return Number.isFinite(amount) ? { budget: amount, currency } : null;
}

function parseTravelers(message: string): number | null {
  const numeric = message.match(/\b(\d+)\s*(?:travelers?|travellers?|people|persons?)\b/i);
  if (numeric) return Number(numeric[1]);
  const worded = message.match(/\b(one|two|three|four|five|six)\s*(?:travelers?|travellers?|people|persons?|of us)\b/i);
  if (worded) return NUMBER_WORDS[worded[1].toLowerCase()] ?? null;
  if (/\bwith my (?:sister|brother|partner|friend|wife|husband)\b/i.test(message)) return 2;
  if (/\b(?:solo|by myself|just me)\b/i.test(message)) return 1;
  return null;
}

function parseLocation(message: string, kind: "origin" | "destination"): string | null {
  if (kind === "destination") {
    if (/\b(?:seoul|south korea|korea)\b/i.test(message)) return "Seoul";
    if (/\b(?:istanbul|türkiye|turkiye|turkey)\b/i.test(message)) return "Istanbul";
  }
  const expression = kind === "origin"
    ? /\bfrom\s+([a-zÀ-ÿ][a-zÀ-ÿ .'-]*?)(?=\s+to\b|,|\.|\s+(?:in|around|for|with|on)\b|$)/i
    : /\bto\s+([a-zÀ-ÿ][a-zÀ-ÿ .'-]*?)(?=,|\.|\s+(?:in|around|for|with|on)\b|$)/i;
  const match = message.match(expression);
  if (match) return titleCase(match[1]);
  return null;
}

export function extractMissionPatch(message: string): Partial<TripRequest> {
  const patch: Partial<TripRequest> = {};
  const origin = parseLocation(message, "origin");
  const destination = parseLocation(message, "destination");
  if (origin) patch.origin = origin;
  if (destination) patch.destination = destination;
  const duration = message.match(/\b(\d{1,2})\s*(?:day|days)\b/i);
  if (duration) patch.duration_days = Number(duration[1]);
  const dateText = message.match(new RegExp(`\\b(${MONTHS.join("|")})(?:\\s+(\\d{1,2})(?!\\d)(?:st|nd|rd|th)?)?(?:,?\\s+(\\d{4}))?`, "i"));
  if (dateText) patch.start_date_text = [titleCase(dateText[1]), dateText[2], dateText[3]].filter(Boolean).join(" ");
  const travelers = parseTravelers(message);
  if (travelers) patch.travelers = travelers;
  const money = parseMoney(message);
  if (money) Object.assign(patch, money);
  const interests = INTERESTS.filter((interest) => new RegExp(`\\b${interest}\\b`, "i").test(message))
    .map((interest) => interest === "cafes" ? "cafés" : interest);
  if (interests.length) patch.interests = [...new Set(interests)];
  if (/\b(?:relaxed|slow pace|not (?:too )?rushed|(?:don't|don’t) want (?:a )?rushed|unhurried)\b/i.test(message)) patch.travel_style = "Relaxed pace";
  else if (/\b(?:luxury|premium)\b/i.test(message)) patch.travel_style = "Luxury";
  else if (/\b(?:on a budget|budget-friendly|backpacking)\b/i.test(message)) patch.travel_style = "Budget conscious";
  return patch;
}

export function applyMissionMessage(current: TripRequest, message: string): TripRequest {
  const patch = extractMissionPatch(message);
  const interests = patch.interests ? [...new Set([...current.interests, ...patch.interests])] : current.interests;
  return { ...current, ...patch, interests };
}

export function getMissingRequirements(request: TripRequest): MissingRequirement[] {
  const missing: MissingRequirement[] = [];
  if (!request.origin) missing.push("origin");
  if (!request.destination) missing.push("destination");
  if (!request.start_date && !request.start_date_text) missing.push("start_date");
  if (!request.end_date && !request.duration_days) missing.push("end_date_or_duration");
  if (!request.travelers) missing.push("travelers");
  if (request.budget === null) missing.push("budget");
  return missing;
}

const COPY: Record<MissingRequirement, string> = {
  origin: "departure city", destination: "destination", start_date: "travel dates",
  start_date_year: "travel year", end_date_or_duration: "trip duration or end date",
  travelers: "number of travelers", budget: "approximate budget",
};

export function buildClarification(request: TripRequest): string | null {
  const missing = getMissingRequirements(request);
  if (!missing.length) return null;
  const known = [request.destination, request.duration_days ? `${request.duration_days} days` : null].filter(Boolean).join(" for ");
  const preferences = request.interests.length ? ` and your ${request.interests.join(" + ")} preferences` : "";
  const fields = missing.map((field) => COPY[field]);
  const last = fields.pop();
  const list = fields.length ? `${fields.join(", ")} and ${last}` : last;
  return `${known ? `I’ve got ${known}${preferences}. ` : ""}Before I plan properly, tell me your ${list}. You can give me everything in one message.`;
}

export type ExecutionStepState = "waiting" | "active" | "complete";
export type ExecutionStep = { id: string; label: string; state: ExecutionStepState };
const STATUS_ORDER: TripStatus[] = ["collecting", "researching_destination", "destination_researched", "researching_flights", "flights_researched", "researching_hotels", "hotels_researched", "researching_activities", "activities_researched", "planning_itinerary", "itinerary_planned"];

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
  return steps.map(({ id, label, start, done }) => ({ id, label, state: current >= done ? "complete" : current >= start ? "active" : "waiting" }));
}
