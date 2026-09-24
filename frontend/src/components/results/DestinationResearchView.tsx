import type { DestinationResearch } from "@/types/trip";

export default function DestinationResearchView({ research }: { research: DestinationResearch }) {
  return (
    <section aria-labelledby="destination-research-title" className="space-y-6">
      <header className="max-w-2xl">
        <p className="eyebrow">Destination intelligence</p>
        <h2 id="destination-research-title" className="section-title">A useful read on {research.destination}</h2>
        <p className="section-copy">Research organized around where to base yourself, what deserves time, and how to move through the city.</p>
      </header>
      <div className="grid gap-5 lg:grid-cols-[1.25fr_.75fr]">
        <div className="glass-panel p-6 sm:p-8">
          <p className="eyebrow">Where to base yourself</p>
          <div className="mt-5 divide-y divide-stone-900/7">
            {research.neighborhoods.map((area, index) => (
              <article key={area.name} className="grid gap-3 py-5 first:pt-0 sm:grid-cols-[2.5rem_1fr]">
                <span className="font-serif text-2xl italic text-[#bd7851]">0{index + 1}</span>
                <div><h3 className="font-semibold text-stone-900">{area.name}</h3><p className="mt-1 text-sm leading-6 text-stone-500">{area.description}</p></div>
              </article>
            ))}
          </div>
        </div>
        <aside className="rounded-[26px] bg-[#eee6da] p-6 sm:p-8">
          <p className="eyebrow">On the ground</p>
          <ul className="mt-5 space-y-4">
            {[...research.transportation, ...research.practical_tips].map((tip) => (
              <li key={tip} className="flex gap-3 text-sm leading-6 text-stone-700"><span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#bd7851]" />{tip}</li>
            ))}
          </ul>
        </aside>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {research.attractions.map((attraction) => (
          <article key={attraction.name} className="rounded-[22px] border border-black/[0.06] bg-white/65 p-5 backdrop-blur-md">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#a96542]">Worth your time</p>
            <h3 className="mt-3 text-lg font-semibold tracking-[-0.02em] text-stone-900">{attraction.name}</h3>
            <p className="mt-2 text-sm leading-6 text-stone-500">{attraction.description}</p>
          </article>
        ))}
      </div>
      {research.sources.length > 0 && <div className="flex flex-wrap items-center gap-2 text-xs text-stone-400"><span>Research sources</span>{research.sources.map((source) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer" className="rounded-full border border-black/[0.07] bg-white/60 px-3 py-1.5 text-stone-600 hover:text-stone-950">{source.title} ↗</a>)}</div>}
    </section>
  );
}
