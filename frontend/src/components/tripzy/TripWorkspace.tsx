"use client";

import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import DestinationTransition from "@/components/destination/DestinationTransition";
import ActivitiesView from "@/components/results/ActivitiesView";
import DestinationResearchView from "@/components/results/DestinationResearchView";
import ItineraryView from "@/components/results/ItineraryView";
import TravelOptionsView from "@/components/results/TravelOptionsView";
import PlanningScope from "@/components/tripzy/PlanningScope";
import TripBrief from "@/components/tripzy/TripBrief";
import TripComposer from "@/components/tripzy/TripComposer";
import WorkspaceNav from "@/components/tripzy/WorkspaceNav";
import {
  EmptyArtifact,
  IntakePrompt,
  PlanningPending,
  TripNotFound,
  WorkspaceLoadError,
} from "@/components/tripzy/WorkspaceStates";
import { clearPendingMission, getPendingMission } from "@/lib/mission-handoff";
import {
  getTrip,
  sendTripMessage,
  TripzyApiError,
  userFacingApiError,
} from "@/lib/tripzy-api";
import type { TripState, TripStateResponse, WorkspaceSection } from "@/types/trip";

type FailedMessage = {
  message: string;
  baseline: string;
  validationError: boolean;
};

function stateSignature(state: TripState): string {
  return JSON.stringify(state);
}

export function isPristineTrip(state: TripState): boolean {
  const request = state.request;
  return (
    state.status === "collecting" &&
    request.origin === null &&
    request.destination === null &&
    request.start_date === null &&
    request.end_date === null &&
    request.start_date_text === null &&
    request.end_date_text === null &&
    request.duration_days === null &&
    request.travelers === null &&
    request.budget === null &&
    request.interests.length === 0 &&
    request.travel_style === null &&
    state.destination_research === null &&
    state.flight_options.length === 0 &&
    state.hotel_options.length === 0 &&
    state.activity_options.length === 0 &&
    state.itinerary === null
  );
}

export default function TripWorkspace({
  tripId,
  activeSection,
}: {
  tripId: string;
  activeSection: WorkspaceSection;
}) {
  const [trip, setTrip] = useState<TripStateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [processingMessage, setProcessingMessage] = useState(false);
  const [failedMessage, setFailedMessage] = useState<FailedMessage | null>(null);
  const [messageError, setMessageError] = useState<string | null>(null);
  const restoredTripRef = useRef<string | null>(null);
  const processingRef = useRef(false);

  const processMessage = useCallback(async (
    message: string,
    baseline: TripStateResponse,
  ): Promise<boolean> => {
    if (processingRef.current) {
      return false;
    }

    processingRef.current = true;
    setProcessingMessage(true);
    setMessageError(null);
    setFailedMessage(null);

    try {
      const response = await sendTripMessage(tripId, message);
      clearPendingMission(tripId);

      try {
        const restored = await getTrip(tripId);
        setTrip({
          ...restored,
          clarification: response.missing_information.length > 0
            ? response.response
            : restored.clarification,
        });
        setLoadError(null);
      } catch (caught) {
        setLoadError(userFacingApiError(caught));
      }

      return true;
    } catch (caught) {
      if (caught instanceof TripzyApiError && caught.code === "not_found") {
        setTrip(null);
        setNotFound(true);
        return false;
      }

      setFailedMessage({
        message,
        baseline: stateSignature(baseline.state),
        validationError: caught instanceof TripzyApiError && caught.code === "validation",
      });
      setMessageError(userFacingApiError(caught));
      return false;
    } finally {
      processingRef.current = false;
      setProcessingMessage(false);
    }
  }, [tripId]);

  const restoreTrip = useCallback(async () => {
    setLoading(true);
    setNotFound(false);
    setLoadError(null);

    try {
      const restored = await getTrip(tripId);
      setTrip(restored);

      const pendingMission = getPendingMission(tripId);
      if (pendingMission) {
        if (isPristineTrip(restored.state)) {
          await processMessage(pendingMission, restored);
        } else {
          clearPendingMission(tripId);
        }
      }
    } catch (caught) {
      if (caught instanceof TripzyApiError && caught.code === "not_found") {
        setNotFound(true);
      } else {
        setLoadError(userFacingApiError(caught));
      }
    } finally {
      setLoading(false);
    }
  }, [processMessage, tripId]);

  useEffect(() => {
    if (restoredTripRef.current === tripId) {
      return;
    }

    restoredTripRef.current = tripId;
    void restoreTrip();
  }, [restoreTrip, tripId]);

  const retryFailedMessage = async () => {
    if (!failedMessage || processingRef.current) {
      return;
    }

    processingRef.current = true;
    setProcessingMessage(true);
    setMessageError(null);

    try {
      const current = await getTrip(tripId);
      setTrip(current);

      if (stateSignature(current.state) !== failedMessage.baseline) {
        clearPendingMission(tripId);
        setFailedMessage(null);
        return;
      }

      processingRef.current = false;
      setProcessingMessage(false);
      await processMessage(failedMessage.message, current);
    } catch (caught) {
      if (caught instanceof TripzyApiError && caught.code === "not_found") {
        setTrip(null);
        setNotFound(true);
      } else {
        setMessageError(userFacingApiError(caught));
      }
    } finally {
      processingRef.current = false;
      setProcessingMessage(false);
    }
  };

  const destination = trip?.state.request.destination ?? undefined;

  if (loading || processingMessage) {
    return (
      <main className="relative flex min-h-screen items-center overflow-x-hidden bg-[#faf8f4] px-5 py-12 sm:px-8">
        <DestinationTransition destination={destination} />
        <div className="relative z-10 w-full"><PlanningPending /></div>
      </main>
    );
  }

  if (notFound) {
    return (
      <main className="relative flex min-h-screen items-center overflow-x-hidden bg-[#faf8f4] px-5 py-12 sm:px-8">
        <DestinationTransition />
        <div className="relative z-10 w-full"><TripNotFound /></div>
      </main>
    );
  }

  if (loadError || !trip) {
    return (
      <main className="relative flex min-h-screen items-center overflow-x-hidden bg-[#faf8f4] px-5 py-12 sm:px-8">
        <DestinationTransition destination={destination} />
        <div className="relative z-10 w-full">
          <WorkspaceLoadError message={loadError ?? "Tripzy could not restore this trip."} onRetry={() => {
            restoredTripRef.current = null;
            void restoreTrip();
          }} />
        </div>
      </main>
    );
  }

  const pristine = isPristineTrip(trip.state);
  const needsClarification = trip.missing_information.length > 0 && !pristine;

  if (pristine || needsClarification) {
    const prompt = pristine
      ? "This workspace is ready. Share the whole trip in one natural message."
      : trip.clarification ?? "Tripzy needs a little more information before planning.";

    return (
      <main className="relative min-h-screen overflow-x-hidden bg-[#faf8f4]">
        <DestinationTransition destination={destination} />
        <section className="relative z-10 mx-auto flex min-h-screen w-full max-w-5xl items-center px-5 py-12 sm:px-8">
          <div className="w-full">
            <Link href="/" className="mb-8 inline-flex text-xs font-semibold uppercase tracking-[0.22em] text-stone-500">← New trip</Link>
            <div className="grid gap-6 lg:grid-cols-[.9fr_1.1fr] lg:items-center">
              <div>
                <IntakePrompt pristine={pristine} prompt={prompt} />
                {messageError && <div role="alert" className="mt-5 rounded-2xl border border-[#b66f49]/20 bg-white/70 px-4 py-3 text-sm text-stone-700">{messageError}</div>}
                <div className="mt-7">
                  {failedMessage && !failedMessage.validationError ? (
                    <div>
                      <blockquote className="rounded-2xl bg-white/55 p-4 text-sm leading-6 text-stone-600">{failedMessage.message}</blockquote>
                      <button type="button" onClick={() => void retryFailedMessage()} className="mt-4 rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-white">Retry safely</button>
                    </div>
                  ) : (
                    <TripComposer
                      key={failedMessage?.message ?? "trip-message"}
                      mode={pristine ? "mission" : "clarification"}
                      initialMessage={failedMessage?.message}
                      onSubmit={(message) => processMessage(message, trip)}
                    />
                  )}
                </div>
              </div>
              <TripBrief request={trip.state.request} />
            </div>
          </div>
        </section>
      </main>
    );
  }

  const state = trip.state;

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#faf8f4]">
      <DestinationTransition destination={destination} quiet />
      <div className="relative z-10 mx-auto w-full max-w-6xl px-5 pb-20 pt-6 sm:px-8 lg:px-10">
        <header className="mb-7 flex items-center justify-between gap-4">
          <Link href="/" className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-700">← New trip</Link>
          <p className="hidden text-xs text-stone-400 sm:block">Give me the trip. I’ll take it from here.</p>
        </header>
        <WorkspaceNav active={activeSection} tripId={tripId} />

        <AnimatePresence mode="wait" initial={false}>
          <motion.div key={activeSection} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25 }} className="mt-8">
            {activeSection === "brief" && <div className="space-y-6"><TripBrief request={state.request} /><PlanningScope status={state.status} /></div>}
            {activeSection === "research" && (
              <div className="space-y-14">
                {state.destination_research ? <DestinationResearchView research={state.destination_research} /> : <EmptyArtifact title="Destination research is unavailable" copy="Tripzy has not persisted supported destination research for this trip." />}
                <ActivitiesView activities={state.activity_options} />
              </div>
            )}
            {activeSection === "options" && <TravelOptionsView flights={state.flight_options} hotels={state.hotel_options} />}
            {activeSection === "itinerary" && (state.itinerary ? <ItineraryView itinerary={state.itinerary} /> : <EmptyArtifact title="Itinerary is unavailable" copy="No structured itinerary has been persisted for this trip yet." />)}
          </motion.div>
        </AnimatePresence>

        <p className="mx-auto mt-16 max-w-2xl border-t border-stone-900/8 pt-8 text-center text-xs leading-5 text-stone-400">This itinerary reflects the current persisted plan. Natural corrections and replanning will arrive in M16B.</p>
      </div>
    </main>
  );
}
