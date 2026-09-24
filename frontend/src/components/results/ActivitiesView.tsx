import type { ActivityOption } from "@/types/trip";

export default function ActivitiesView({ activities }: { activities: ActivityOption[] }) {
  return (
    <section aria-labelledby="activities-title">
      <header className="mb-6 max-w-2xl">
        <p className="eyebrow">Experiences</p>
        <h2 id="activities-title" className="section-title">The texture of the trip</h2>
        <p className="section-copy">A considered shortlist for the itinerary, grouped by place and pace rather than a tourist checklist.</p>
      </header>
      <div className="divide-y divide-stone-900/8 rounded-[26px] border border-black/[0.06] bg-white/68 px-5 backdrop-blur-md sm:px-8">
        {activities.length ? activities.map((activity, index) => (
          <article key={activity.name} className="grid gap-4 py-6 sm:grid-cols-[3rem_1fr_auto] sm:items-center">
            <span className="font-serif text-2xl italic text-[#bd7851]">0{index + 1}</span>
            <div><div className="flex flex-wrap items-center gap-2"><h3 className="font-semibold text-stone-900">{activity.name}</h3>{activity.category && <span className="detail-pill">{activity.category}</span>}</div>{activity.description && <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-500">{activity.description}</p>}</div>
            <div className="text-xs text-stone-400 sm:text-right"><p>{activity.neighborhood ?? activity.destination}</p><p className="mt-1 font-medium text-stone-600">{activity.estimated_duration ?? "Flexible"}</p></div>
          </article>
        )) : <p className="py-8 text-sm text-stone-500">No supported activities were returned.</p>}
      </div>
    </section>
  );
}
