import Link from "next/link";

export function PlanningPending() {
  return (
    <section role="status" aria-live="polite" className="glass-panel mx-auto max-w-2xl p-8 text-center sm:p-12">
      <div aria-hidden="true" className="mx-auto h-10 w-10 animate-pulse rounded-full border border-[#b66f49]/30 bg-[#e8b38c]/35" />
      <p className="eyebrow mt-6">Planning in progress</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-stone-950 sm:text-4xl">Tripzy is planning your trip…</h1>
      <p className="mx-auto mt-4 max-w-lg text-sm leading-6 text-stone-500">Tripzy is researching the journey and building your itinerary. This request can take a little while.</p>
    </section>
  );
}

export function IntakePrompt({ pristine, prompt }: { pristine: boolean; prompt: string }) {
  return (
    <div>
      <p className="eyebrow">{pristine ? "Your trip workspace" : "One clarification"}</p>
      <h1 className="mt-3 text-4xl font-semibold leading-[1] tracking-[-0.045em] text-stone-950 sm:text-5xl">{pristine ? "Tell me the whole mission." : "I understand the shape of it."}</h1>
      <p className="mt-5 max-w-xl text-base leading-7 text-stone-600">{prompt}</p>
    </div>
  );
}

export function TripNotFound() {
  return (
    <section className="glass-panel mx-auto max-w-xl p-8 text-center sm:p-12">
      <p className="eyebrow">Unknown trip</p>
      <h1 className="mt-3 text-4xl font-semibold tracking-[-0.045em] text-stone-950">Trip not found</h1>
      <p className="mt-4 text-sm leading-6 text-stone-500">This trip link may be incorrect, or the persisted trip is no longer available.</p>
      <Link href="/" className="mt-7 inline-flex rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-black">Start a new trip</Link>
    </section>
  );
}

export function WorkspaceLoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <section role="alert" className="glass-panel mx-auto max-w-xl p-8 text-center sm:p-12">
      <p className="eyebrow">Couldn’t restore trip</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-stone-950">Your trip is still yours.</h1>
      <p className="mt-4 text-sm leading-6 text-stone-500">{message}</p>
      <div className="mt-7 flex flex-wrap justify-center gap-3">
        <button type="button" onClick={onRetry} className="rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-black">Try again</button>
        <Link href="/" className="rounded-full border border-stone-900/10 bg-white/70 px-5 py-3 text-sm font-semibold text-stone-700">New trip</Link>
      </div>
    </section>
  );
}

export function EmptyArtifact({ title, copy }: { title: string; copy: string }) {
  return (
    <section className="rounded-[24px] border border-dashed border-stone-300 bg-white/45 p-8">
      <p className="text-sm font-semibold text-stone-800">{title}</p>
      <p className="mt-2 text-sm leading-6 text-stone-500">{copy}</p>
    </section>
  );
}
