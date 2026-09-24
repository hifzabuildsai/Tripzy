import type { FlightOption, HotelOption } from "@/types/trip";

function price(value: number | null, currency: string | null) {
  if (value === null) return "Price not found";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: currency ?? "USD", maximumFractionDigits: 0 }).format(value);
}

export default function TravelOptionsView({ flights, hotels }: { flights: FlightOption[]; hotels: HotelOption[] }) {
  return (
    <section aria-labelledby="travel-options-title" className="space-y-8">
      <header className="max-w-2xl">
        <p className="eyebrow">Researched options</p>
        <h2 id="travel-options-title" className="section-title">Routes and stays worth comparing</h2>
        <p className="section-copy">These are research candidates. Prices and availability need to be checked with the source before booking.</p>
      </header>
      <div>
        <div className="mb-4 flex items-center justify-between"><h3 className="text-lg font-semibold text-stone-900">Flight routes</h3><span className="text-xs text-stone-400">{flights.length} options</span></div>
        <div className="space-y-3">
          {flights.length ? flights.map((flight) => (
            <article key={`${flight.airline}-${flight.departure_time}`} className="glass-panel grid gap-5 p-5 sm:grid-cols-[1fr_auto_auto] sm:items-center sm:p-6">
              <div><p className="text-xs text-stone-400">{flight.airline ?? "Airline not specified"}</p><p className="mt-1 font-semibold text-stone-900">{flight.origin} <span className="mx-2 text-stone-300">→</span> {flight.destination}</p></div>
              <div className="flex gap-6 text-sm sm:text-right"><div><p className="text-stone-400">Duration</p><p className="mt-1 font-medium text-stone-800">{flight.duration ?? "—"}</p></div><div><p className="text-stone-400">Stops</p><p className="mt-1 font-medium text-stone-800">{flight.stops === 0 ? "Direct" : flight.stops ?? "—"}</p></div></div>
              <div className="sm:min-w-28 sm:text-right"><p className="text-lg font-semibold text-stone-900">{price(flight.price, flight.currency)}</p><p className="text-[11px] text-stone-400">researched fare</p></div>
            </article>
          )) : <EmptyResult label="No supported flight options were returned." />}
        </div>
      </div>
      <div>
        <div className="mb-4 flex items-center justify-between"><h3 className="text-lg font-semibold text-stone-900">Places to stay</h3><span className="text-xs text-stone-400">{hotels.length} options</span></div>
        <div className="grid gap-4 md:grid-cols-2">
          {hotels.length ? hotels.map((hotel) => (
            <article key={hotel.name} className="rounded-[24px] border border-black/[0.06] bg-white/75 p-6 shadow-[0_18px_55px_rgba(60,45,30,0.06)] backdrop-blur-md">
              <div className="flex items-start justify-between gap-3"><div><p className="text-xs font-medium text-[#a96542]">{hotel.neighborhood ?? hotel.destination}</p><h4 className="mt-1 text-xl font-semibold tracking-[-0.025em] text-stone-900">{hotel.name}</h4></div>{hotel.rating !== null && <span className="rounded-full bg-[#f4eadb] px-2.5 py-1 text-xs font-semibold text-stone-700">★ {hotel.rating}</span>}</div>
              {hotel.description && <p className="mt-4 text-sm leading-6 text-stone-500">{hotel.description}</p>}
              <div className="mt-6 flex items-end justify-between border-t border-stone-900/7 pt-4"><span className="text-xs text-stone-400">Researched rate</span><span className="font-semibold text-stone-900">{price(hotel.price_per_night, hotel.currency)} <small className="font-normal text-stone-400">/ night</small></span></div>
            </article>
          )) : <EmptyResult label="No supported hotel options were returned." />}
        </div>
      </div>
    </section>
  );
}

function EmptyResult({ label }: { label: string }) {
  return <div className="rounded-[22px] border border-dashed border-stone-300 bg-white/40 p-8 text-sm text-stone-500">{label}</div>;
}
