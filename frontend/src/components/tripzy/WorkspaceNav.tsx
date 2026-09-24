import type { WorkspaceSection } from "@/types/trip";

const ITEMS: { id: WorkspaceSection; label: string }[] = [
  { id: "brief", label: "Trip brief" }, { id: "research", label: "Discover" },
  { id: "options", label: "Options" }, { id: "itinerary", label: "Itinerary" },
];

export default function WorkspaceNav({ active, onChange }: { active: WorkspaceSection; onChange: (value: WorkspaceSection) => void }) {
  return (
    <nav aria-label="Trip workspace" className="sticky top-3 z-30 mx-auto flex w-fit max-w-full gap-1 overflow-x-auto rounded-full border border-black/[0.07] bg-white/85 p-1.5 shadow-[0_10px_35px_rgba(55,43,30,0.08)] backdrop-blur-xl">
      {ITEMS.map((item) => (
        <button key={item.id} type="button" onClick={() => onChange(item.id)} aria-current={active === item.id ? "page" : undefined}
          className={`whitespace-nowrap rounded-full px-4 py-2 text-xs font-medium transition ${active === item.id ? "bg-stone-900 text-white" : "text-stone-500 hover:bg-stone-100 hover:text-stone-900"}`}>
          {item.label}
        </button>
      ))}
    </nav>
  );
}
