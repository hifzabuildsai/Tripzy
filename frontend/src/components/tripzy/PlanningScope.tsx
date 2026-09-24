import { mapStatusToExecution } from "@/lib/trip-status";
import type { TripStatus } from "@/types/trip";

export default function PlanningScope({ status }: { status: TripStatus }) {
  const steps = mapStatusToExecution(status);
  return (
    <section aria-labelledby="scope-title" className="rounded-[26px] bg-[#1d2924] p-6 text-white shadow-[0_24px_70px_rgba(39,50,43,0.16)] sm:p-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/50">Planning scope</p>
          <h2 id="scope-title" className="mt-2 text-2xl font-semibold tracking-[-0.03em]">I have what I need. I’ll take it from here.</h2>
        </div>
        <span className="w-fit rounded-full border border-white/15 px-3 py-1 text-xs text-white/65">Persisted trip state</span>
      </div>
      <ol className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map((step, index) => (
          <li key={step.id} className="flex items-center gap-3 rounded-2xl bg-white/[0.065] p-3.5">
            <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${step.state === "complete" ? "bg-[#d8e6c9] text-[#253526]" : step.state === "active" ? "bg-[#e8b38c] text-[#4a2714]" : "bg-white/10 text-white/65"}`}>
              {step.state === "complete" ? "✓" : index + 1}
            </span>
            <span className={step.state !== "waiting" ? "text-sm text-white/90" : "text-sm text-white/45"}>{step.label}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
