import TripWorkspace from "@/components/tripzy/TripWorkspace";
import { normalizeWorkspaceSection } from "@/lib/trip-status";

export default async function TripPage({
  params,
  searchParams,
}: {
  params: Promise<{ tripId: string }>;
  searchParams: Promise<{ view?: string | string[] }>;
}) {
  const [{ tripId }, query] = await Promise.all([params, searchParams]);
  const rawView = Array.isArray(query.view) ? query.view[0] : query.view;

  return (
    <TripWorkspace
      tripId={tripId}
      activeSection={normalizeWorkspaceSection(rawView)}
    />
  );
}
