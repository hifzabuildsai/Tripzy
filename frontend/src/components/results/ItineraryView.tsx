import type { Itinerary } from "@/types/trip";

function formatCost(value: number | null, currency: string | null) {
  if (value === null) return null;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: currency ?? "USD", maximumFractionDigits: 0 }).format(value);
}

export default function ItineraryView({ itinerary }: { itinerary: Itinerary }) {
  return (
    <section aria-labelledby="itinerary-title">
      <header className="relative overflow-hidden rounded-[30px] bg-[#26352d] px-6 py-9 text-white shadow-[0_28px_80px_rgba(38,53,45,0.17)] sm:px-10 sm:py-12">
        <div className="absolute -right-12 -top-20 h-64 w-64 rounded-full bg-[#c7855d]/20 blur-3xl" />
        <div className="relative grid gap-8 md:grid-cols-[1fr_auto] md:items-end">
          <div><p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/48">Your journey</p><h2 id="itinerary-title" className="mt-3 max-w-xl text-4xl font-semibold leading-[.98] tracking-[-0.045em] sm:text-5xl">{itinerary.destination}, day by day.</h2><p className="mt-4 max-w-xl text-sm leading-6 text-white/60">A paced plan built from the researched places and your current trip brief.</p></div>
          <dl className="grid grid-cols-3 gap-6 border-t border-white/10 pt-5 text-right md:border-l md:border-t-0 md:pl-8 md:pt-0"><div><dt className="text-[10px] uppercase tracking-wider text-white/40">Days</dt><dd className="mt-1 text-lg font-semibold">{itinerary.days.length}</dd></div><div><dt className="text-[10px] uppercase tracking-wider text-white/40">Travelers</dt><dd className="mt-1 text-lg font-semibold">{itinerary.travelers}</dd></div><div><dt className="text-[10px] uppercase tracking-wider text-white/40">Start</dt><dd className="mt-1 text-sm font-semibold">{itinerary.start_date}</dd></div></dl>
        </div>
      </header>
      <div className="mx-auto max-w-4xl py-5 sm:py-8">
        {itinerary.days.map((day) => (
          <article key={day.day_number} className="grid gap-5 border-b border-stone-900/8 py-8 last:border-0 sm:grid-cols-[7.5rem_1fr] sm:gap-8">
            <header><p className="eyebrow">Day {day.day_number}</p><h3 className="mt-2 text-xl font-semibold leading-6 tracking-[-0.025em] text-stone-900">{day.title ?? "Open day"}</h3>{day.date && <p className="mt-2 text-xs text-stone-400">{day.date}</p>}</header>
            <div className="space-y-3">
              {day.items.map((item) => (
                <div key={`${item.start_time}-${item.title}`} className="group grid gap-3 rounded-[20px] bg-white/65 p-5 transition hover:bg-white sm:grid-cols-[4.5rem_1fr_auto]">
                  <time className="text-xs font-semibold text-[#a96542]">{item.start_time ?? "Flexible"}</time>
                  <div><div className="flex flex-wrap items-center gap-2"><h4 className="font-semibold text-stone-900">{item.title}</h4>{item.category && <span className="text-[10px] uppercase tracking-wider text-stone-400">{item.category}</span>}</div>{item.description && <p className="mt-1.5 text-sm leading-6 text-stone-500">{item.description}</p>}{item.notes.length > 0 && <p className="mt-2 text-xs italic text-stone-400">{item.notes[0]}</p>}</div>
                  <div className="text-xs text-stone-400 sm:text-right"><p>{item.neighborhood}</p>{formatCost(item.estimated_cost, item.currency) && <p className="mt-1 font-medium text-stone-600">~{formatCost(item.estimated_cost, item.currency)}</p>}</div>
                </div>
              ))}
              {day.notes.map((note) => <p key={note} className="px-2 text-xs italic text-stone-400">{note}</p>)}
            </div>
          </article>
        ))}
      </div>
      {itinerary.planning_notes.length > 0 && <aside className="rounded-[22px] bg-[#eee6da] p-5"><p className="eyebrow">Planning notes</p><ul className="mt-3 space-y-2 text-sm text-stone-600">{itinerary.planning_notes.map((note) => <li key={note}>• {note}</li>)}</ul></aside>}
    </section>
  );
}
