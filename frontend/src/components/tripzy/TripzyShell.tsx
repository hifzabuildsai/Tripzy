"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";

import DestinationTransition from "@/components/destination/DestinationTransition";
import ActivitiesView from "@/components/results/ActivitiesView";
import DestinationResearchView from "@/components/results/DestinationResearchView";
import ItineraryView from "@/components/results/ItineraryView";
import TravelOptionsView from "@/components/results/TravelOptionsView";
import PlanningScope from "@/components/tripzy/PlanningScope";
import TripBrief from "@/components/tripzy/TripBrief";
import TripComposer from "@/components/tripzy/TripComposer";
import WorkspaceNav from "@/components/tripzy/WorkspaceNav";
import { buildPreviewState } from "@/data/demo-trip";
import { applyMissionMessage, buildClarification, EMPTY_TRIP_REQUEST, getMissingRequirements } from "@/lib/mission-intake";
import type { TripRequest, WorkspaceSection } from "@/types/trip";

export default function TripzyShell() {
  const [request, setRequest] = useState<TripRequest>(EMPTY_TRIP_REQUEST);
  const [missionStarted, setMissionStarted] = useState(false);
  const [activeSection, setActiveSection] = useState<WorkspaceSection>("brief");

  const missing = getMissingRequirements(request);
  const complete = missionStarted && missing.length === 0;
  const clarification = missionStarted ? buildClarification(request) : null;
  const preview = useMemo(() => complete ? buildPreviewState(request) : null, [complete, request]);

  const handleMessage = (message: string) => {
    setMissionStarted(true);
    setRequest((current) => applyMissionMessage(current, message));
  };

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#faf8f4]">
      <DestinationTransition destination={request.destination ?? undefined} quiet={complete} />

      {!missionStarted ? (
        <section className="relative z-10 flex min-h-screen items-center justify-center px-5 py-12 sm:px-8">
          <div className="w-full max-w-4xl text-center">
            <p className="mb-5 text-xs font-semibold uppercase tracking-[0.26em] text-stone-500">Tripzy</p>
            <h1 className="text-[46px] font-semibold leading-[0.94] tracking-[-0.052em] text-stone-950 sm:text-7xl lg:text-[82px]">
              Give me the trip.<br /><span className="font-serif font-normal italic text-[#b66f49]">I’ll take it from here.</span>
            </h1>
            <p className="mx-auto mb-9 mt-6 max-w-xl text-sm leading-6 text-stone-500 sm:text-base sm:leading-7">Share the whole mission in your own words. Tripzy turns it into a structured plan, researches the journey and builds the days.</p>
            <TripComposer onSubmit={handleMessage} />
          </div>
        </section>
      ) : !complete ? (
        <section className="relative z-10 mx-auto flex min-h-screen w-full max-w-5xl items-center px-5 py-12 sm:px-8">
          <div className="grid w-full gap-6 lg:grid-cols-[.9fr_1.1fr] lg:items-center">
            <div>
              <button type="button" onClick={() => { setMissionStarted(false); setRequest(EMPTY_TRIP_REQUEST); }} className="mb-8 text-xs font-semibold uppercase tracking-[0.22em] text-stone-500">Tripzy</button>
              <p className="eyebrow">One clarification</p>
              <h1 className="mt-3 text-4xl font-semibold leading-[1] tracking-[-0.045em] text-stone-950 sm:text-5xl">I understand the shape of it.</h1>
              <p className="mt-5 max-w-xl text-base leading-7 text-stone-600">{clarification}</p>
              <div className="mt-7"><TripComposer mode="revision" onSubmit={handleMessage} /></div>
            </div>
            <TripBrief request={request} />
          </div>
        </section>
      ) : preview ? (
        <div className="relative z-10 mx-auto w-full max-w-6xl px-5 pb-20 pt-6 sm:px-8 lg:px-10">
          <header className="mb-7 flex items-center justify-between">
            <button type="button" onClick={() => { setMissionStarted(false); setRequest(EMPTY_TRIP_REQUEST); setActiveSection("brief"); }} className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-700">Tripzy</button>
            <p className="hidden text-xs text-stone-400 sm:block">Give me the trip. I’ll take it from here.</p>
          </header>
          <WorkspaceNav active={activeSection} onChange={setActiveSection} />

          <AnimatePresence mode="wait" initial={false}>
            <motion.div key={activeSection} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25 }} className="mt-8">
              {activeSection === "brief" && <div className="space-y-6"><TripBrief request={request} /><PlanningScope status={preview.status} preview /></div>}
              {activeSection === "research" && preview.destination_research && <div className="space-y-14"><DestinationResearchView research={preview.destination_research} /><ActivitiesView activities={preview.activity_options} /></div>}
              {activeSection === "options" && <TravelOptionsView flights={preview.flight_options} hotels={preview.hotel_options} />}
              {activeSection === "itinerary" && preview.itinerary && <ItineraryView itinerary={preview.itinerary} />}
            </motion.div>
          </AnimatePresence>

          <section aria-labelledby="revise-title" className="mx-auto mt-16 max-w-3xl border-t border-stone-900/8 pt-9 text-center">
            <p className="eyebrow">Keep shaping it</p>
            <h2 id="revise-title" className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-stone-900">Change your mind naturally.</h2>
            <p className="mx-auto mb-5 mt-2 max-w-lg text-sm leading-6 text-stone-500">Try: “Actually make it Istanbul, same dates, raise the budget to $3,000, and focus more on food.”</p>
            <TripComposer mode="revision" onSubmit={handleMessage} />
          </section>
        </div>
      ) : null}
    </main>
  );
}
