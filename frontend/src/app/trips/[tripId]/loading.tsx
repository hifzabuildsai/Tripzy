import { PlanningPending } from "@/components/tripzy/WorkspaceStates";

export default function LoadingTrip() {
  return (
    <main className="flex min-h-screen items-center bg-[#faf8f4] px-5 py-12 sm:px-8">
      <div className="w-full"><PlanningPending /></div>
    </main>
  );
}
