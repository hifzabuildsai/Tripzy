"use client";

import { useState } from "react";

import DestinationTransition from "@/components/destination/DestinationTransition";
import TripComposer from "@/components/tripzy/TripComposer";
import TripSignature from "@/components/tripzy/TripSignature";

import type {
  TripIntent,
  TripSeason,
} from "@/types/trip";

function extractSeason(
  message: string,
): TripSeason | undefined {
  const lower = message.toLowerCase();

  if (lower.includes("spring")) {
    return "spring";
  }

  if (lower.includes("summer")) {
    return "summer";
  }

  if (
    lower.includes("autumn") ||
    lower.includes("fall")
  ) {
    return "autumn";
  }

  if (lower.includes("winter")) {
    return "winter";
  }

  return undefined;
}

function extractDuration(
  message: string,
): number | undefined {
  const match = message.match(
    /\b(\d{1,2})\s*(?:day|days)\b/i,
  );

  if (!match) {
    return undefined;
  }

  const duration = Number(match[1]);

  if (
    Number.isNaN(duration) ||
    duration < 1 ||
    duration > 60
  ) {
    return undefined;
  }

  return duration;
}

function extractDestination(
  message: string,
): Pick<
  TripIntent,
  "destination" | "country"
> {
  const lower = message
    .trim()
    .toLowerCase();

  if (
    lower.includes("seoul") ||
    lower.includes("south korea") ||
    lower.includes("korea")
  ) {
    return {
      destination: "Seoul",
      country: "South Korea",
    };
  }

  if (
    lower.includes("istanbul") ||
    lower.includes("turkey") ||
    lower.includes("turkiye") ||
    lower.includes("türkiye")
  ) {
    return {
      destination: "Istanbul",
      country: "Türkiye",
    };
  }

  return {};
}

function createLocalTripIntent(
  message: string,
): TripIntent {
  return {
    rawText: message,
    ...extractDestination(message),
    durationDays: extractDuration(message),
    season: extractSeason(message),
  };
}

export default function TripzyShell() {
  const [tripIntent, setTripIntent] =
    useState<TripIntent | null>(null);

  const handleTripSubmit = (
    message: string,
  ) => {
    setTripIntent(
      createLocalTripIntent(message),
    );
  };

  const hasTripStarted =
    tripIntent !== null;

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#faf8f4]">
      <DestinationTransition
        destination={
          tripIntent?.destination
        }
      />

      <section className="pointer-events-none relative z-10 flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
        <div className="pointer-events-auto w-full max-w-3xl text-center">
          <p className="mb-4 text-xs font-medium uppercase tracking-[0.24em] text-neutral-500 sm:text-sm">
            Tripzy
          </p>

          <h1 className="text-[42px] font-semibold leading-[0.98] tracking-[-0.045em] text-neutral-900 sm:text-6xl lg:text-[68px]">
            {tripIntent?.destination ? (
              <>
                Let&apos;s shape your
                <br />
                {tripIntent.destination} trip.
              </>
            ) : hasTripStarted ? (
              <>
                Let&apos;s shape
                <br />
                your trip.
              </>
            ) : (
              <>
                Where do you want
                <br />
                to go?
              </>
            )}
          </h1>

          <p className="mx-auto mb-8 mt-5 max-w-md text-sm leading-6 text-neutral-500 sm:text-base sm:leading-7">
            {hasTripStarted
              ? "Your idea is taking shape. Keep adding the details that matter to you."
              : "Tell me what kind of trip you're dreaming about."}
          </p>

          <TripComposer
            onSubmit={handleTripSubmit}
          />

          <TripSignature
            intent={tripIntent}
          />
        </div>
      </section>
    </main>
  );
}