"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import DestinationTransition from "@/components/destination/DestinationTransition";
import TripComposer from "@/components/tripzy/TripComposer";
import { createTripForMission } from "@/lib/mission-handoff";
import { userFacingApiError } from "@/lib/tripzy-api";

export default function NewTripLanding() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleMission = async (mission: string): Promise<boolean> => {
    if (submitting) {
      return false;
    }

    setSubmitting(true);
    setError(null);

    try {
      const tripId = await createTripForMission(mission);
      router.push(`/trips/${encodeURIComponent(tripId)}`);
      return true;
    } catch (caught) {
      setError(userFacingApiError(caught));
      return false;
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#faf8f4]">
      <DestinationTransition />
      <section className="relative z-10 flex min-h-screen items-center justify-center px-5 py-12 sm:px-8">
        <div className="w-full max-w-4xl text-center">
          <p className="mb-5 text-xs font-semibold uppercase tracking-[0.26em] text-stone-500">Tripzy</p>
          <h1 className="text-[46px] font-semibold leading-[0.94] tracking-[-0.052em] text-stone-950 sm:text-7xl lg:text-[82px]">
            Give me the trip.<br /><span className="font-serif font-normal italic text-[#b66f49]">I’ll take it from here.</span>
          </h1>
          <p className="mx-auto mb-9 mt-6 max-w-xl text-sm leading-6 text-stone-500 sm:text-base sm:leading-7">Share the whole mission in your own words. Tripzy turns it into a structured plan, researches the journey and builds the days.</p>
          <TripComposer onSubmit={handleMission} disabled={submitting} />
          {submitting && <p role="status" className="mt-5 text-sm text-stone-500">Creating your trip workspace…</p>}
          {error && (
            <div role="alert" className="mx-auto mt-5 max-w-2xl rounded-2xl border border-[#b66f49]/20 bg-white/70 px-5 py-4 text-sm text-stone-700 backdrop-blur-md">
              <p>{error}</p>
              <p className="mt-1 text-xs text-stone-400">Your mission is still here. Submit again when the service is ready.</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
