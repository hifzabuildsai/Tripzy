import type { TripRequest } from "@/types/trip";

type Props = { request: TripRequest; compact?: boolean };

function money(amount: number, currency: string | null) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: currency ?? "USD", maximumFractionDigits: 0 }).format(amount);
}

export default function TripBrief({ request, compact = false }: Props) {
  const details = [
    { label: "Route", value: request.origin && request.destination ? `${request.origin} → ${request.destination}` : request.destination ?? request.origin },
    { label: "When", value: request.start_date ?? request.start_date_text },
    { label: "Length", value: request.duration_days ? `${request.duration_days} days` : request.end_date },
    { label: "Travelers", value: request.travelers ? `${request.travelers} ${request.travelers === 1 ? "traveler" : "travelers"}` : null },
    { label: "Budget", value: request.budget !== null ? money(request.budget, request.currency) : null },
    { label: "Pace", value: request.travel_style },
  ].filter((item): item is { label: string; value: string } => Boolean(item.value));

  return (
    <section aria-labelledby="trip-brief-title" className={`glass-panel ${compact ? "p-5" : "p-6 sm:p-8"}`}>
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Current trip</p>
          <h2 id="trip-brief-title" className="mt-1 text-xl font-semibold tracking-[-0.025em] text-stone-950">Trip Brief</h2>
        </div>
        <span className="rounded-full bg-[#eef3e8] px-3 py-1 text-xs font-medium text-[#466047]">Structured</span>
      </div>
      <dl className="grid grid-cols-2 gap-x-5 gap-y-5 sm:grid-cols-3">
        {details.map(({ label, value }) => (
          <div key={label}>
            <dt className="text-[11px] font-semibold uppercase tracking-[0.13em] text-stone-400">{label}</dt>
            <dd className="mt-1 text-sm font-medium leading-5 text-stone-800">{value}</dd>
          </div>
        ))}
      </dl>
      {request.interests.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2 border-t border-stone-900/6 pt-5" aria-label="Interests">
          {request.interests.map((interest) => <span key={interest} className="detail-pill">{interest}</span>)}
        </div>
      )}
    </section>
  );
}
