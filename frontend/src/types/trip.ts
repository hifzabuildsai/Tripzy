export type TripSeason =
  | "spring"
  | "summer"
  | "autumn"
  | "winter";

export type TripIntent = {
  rawText: string;

  destination?: string;
  country?: string;

  durationDays?: number;
  season?: TripSeason;
};