import { createTrip } from "@/lib/tripzy-api";

const pendingMissions = new Map<string, string>();
const STORAGE_PREFIX = "tripzy:pending-mission:";

function storage(): Storage | null {
  return typeof window === "undefined" ? null : window.sessionStorage;
}

export function setPendingMission(tripId: string, mission: string): void {
  pendingMissions.set(tripId, mission);

  try {
    storage()?.setItem(`${STORAGE_PREFIX}${tripId}`, mission);
  } catch {
    // In-memory handoff still works when browser storage is unavailable.
  }
}

export function getPendingMission(tripId: string): string | null {
  const inMemory = pendingMissions.get(tripId);

  if (inMemory) {
    return inMemory;
  }

  try {
    return storage()?.getItem(`${STORAGE_PREFIX}${tripId}`) ?? null;
  } catch {
    return null;
  }
}

export function clearPendingMission(tripId: string): void {
  pendingMissions.delete(tripId);

  try {
    storage()?.removeItem(`${STORAGE_PREFIX}${tripId}`);
  } catch {
    // Nothing else is required when browser storage is unavailable.
  }
}

type CreateMissionDependencies = {
  create: typeof createTrip;
  remember: typeof setPendingMission;
};

const DEFAULT_DEPENDENCIES: CreateMissionDependencies = {
  create: createTrip,
  remember: setPendingMission,
};

export async function createTripForMission(
  mission: string,
  dependencies: CreateMissionDependencies = DEFAULT_DEPENDENCIES,
): Promise<string> {
  if (!mission.trim()) {
    throw new Error("A trip mission is required.");
  }

  const created = await dependencies.create();
  dependencies.remember(created.trip_id, mission);
  return created.trip_id;
}
