"use client";

import TripComposer from "@/components/tripzy/TripComposer";

export default function TripRevisionPanel({
  open,
  error,
  failedMessage,
  onOpen,
  onSubmit,
  onRetry,
}: {
  open: boolean;
  error: string | null;
  failedMessage: string | null;
  onOpen: () => void;
  onSubmit: (message: string) => Promise<boolean>;
  onRetry: () => void;
}) {
  return (
    <section aria-label="Revise this trip" className="mt-6 rounded-[24px] border border-stone-900/8 bg-white/60 p-5 shadow-[0_16px_50px_rgba(74,55,35,0.06)] backdrop-blur-xl sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Same trip, revised</p>
          <p className="mt-2 text-sm leading-6 text-stone-600">Change dates, budget, travelers, destination, pace or interests in natural language.</p>
        </div>
        {!open && !failedMessage && (
          <button type="button" onClick={onOpen} className="rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-black">Change the plan</button>
        )}
      </div>

      {error && <div role="alert" className="mt-5 rounded-2xl border border-[#b66f49]/20 bg-white/70 px-4 py-3 text-sm text-stone-700">{error}</div>}

      {failedMessage ? (
        <div className="mt-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Correction kept for safe retry</p>
          <blockquote className="mt-3 rounded-2xl bg-white/70 p-4 text-sm leading-6 text-stone-700">{failedMessage}</blockquote>
          <button type="button" onClick={onRetry} className="mt-4 rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-white">Retry this change</button>
        </div>
      ) : open ? (
        <div className="mt-5">
          <TripComposer mode="revision" onSubmit={onSubmit} />
        </div>
      ) : null}
    </section>
  );
}
