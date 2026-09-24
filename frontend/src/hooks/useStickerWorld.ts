"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  createStickerMotion,
  DESKTOP_STICKER_SLOTS,
  MOBILE_STICKER_SLOTS,
  TABLET_STICKER_SLOTS,
} from "@/lib/motion";

import type {
  StickerMotionConfig,
  StickerSlot,
} from "@/lib/motion";

import type { StickerAsset } from "@/types/sticker";

export type StickerSource =
  | "universal"
  | "destination";

export type ActiveSticker = {
  instanceId: string;
  sticker: StickerAsset;
  slot: StickerSlot;
  source: StickerSource;
  motionConfig: StickerMotionConfig;
};

type ViewportMode =
  | "mobile"
  | "tablet"
  | "laptop"
  | "desktop";

type Composition = {
  universal: number;
  destination: number;
};

function shuffle<T>(
  items: readonly T[],
): T[] {
  const copy = [...items];

  for (
    let index = copy.length - 1;
    index > 0;
    index -= 1
  ) {
    const randomIndex = Math.floor(
      Math.random() * (index + 1),
    );

    [copy[index], copy[randomIndex]] = [
      copy[randomIndex],
      copy[index],
    ];
  }

  return copy;
}

function randomBetween(
  min: number,
  max: number,
): number {
  return Math.random() * (max - min) + min;
}

function createInstanceId(): string {
  return `${Date.now()}-${Math.random()
    .toString(36)
    .slice(2)}`;
}

function getViewportMode(
  width: number,
): ViewportMode {
  if (width < 640) {
    return "mobile";
  }

  if (width < 1024) {
    return "tablet";
  }

  if (width < 1440) {
    return "laptop";
  }

  return "desktop";
}

function getSlotsForMode(
  mode: ViewportMode,
): StickerSlot[] {
  if (mode === "mobile") {
    return MOBILE_STICKER_SLOTS;
  }

  if (mode === "tablet") {
    return TABLET_STICKER_SLOTS;
  }

  return DESKTOP_STICKER_SLOTS;
}

function getComposition(
  mode: ViewportMode,
  hasDestination: boolean,
): Composition {
  if (!hasDestination) {
    if (mode === "mobile") {
      return {
        destination: 0,
        universal: 4,
      };
    }

    if (mode === "tablet") {
      return {
        destination: 0,
        universal: 6,
      };
    }

    if (mode === "laptop") {
      return {
        destination: 0,
        universal: 8,
      };
    }

    return {
      destination: 0,
      universal: 9,
    };
  }

  if (mode === "mobile") {
    return {
      destination: 2,
      universal: 2,
    };
  }

  if (mode === "tablet") {
    return {
      destination: 3,
      universal: 4,
    };
  }

  /*
   * Laptop + desktop:
   * 4 destination + 5 universal = 9.
   */
  return {
    destination: 4,
    universal: 5,
  };
}

type PendingSticker = {
  sticker: StickerAsset;
  source: StickerSource;
};

function createInitialWorld(
  universalStickers: readonly StickerAsset[],
  destinationStickers:
    | readonly StickerAsset[]
    | undefined,
  mode: ViewportMode,
): ActiveSticker[] {
  const hasDestination =
    Boolean(
      destinationStickers &&
        destinationStickers.length > 0,
    );

  const composition =
    getComposition(
      mode,
      hasDestination,
    );

  const pending: PendingSticker[] = [];

  if (
    destinationStickers &&
    composition.destination > 0
  ) {
    const selectedDestination =
      shuffle(
        destinationStickers,
      ).slice(
        0,
        composition.destination,
      );

    selectedDestination.forEach(
      (sticker) => {
        pending.push({
          sticker,
          source: "destination",
        });
      },
    );
  }

  const selectedUniversal =
    shuffle(
      universalStickers,
    ).slice(
      0,
      composition.universal,
    );

  selectedUniversal.forEach(
    (sticker) => {
      pending.push({
        sticker,
        source: "universal",
      });
    },
  );

  /*
   * Mix destination + universal together before
   * assigning positions, so destination assets
   * do not cluster in one visual region.
   */
  const shuffledPending =
    shuffle(pending);

  const selectedSlots =
    shuffle(
      getSlotsForMode(mode),
    ).slice(
      0,
      shuffledPending.length,
    );

  return shuffledPending.map(
    (entry, index) => {
      const slot =
        selectedSlots[index];

      return {
        instanceId:
          createInstanceId(),

        sticker:
          entry.sticker,

        source:
          entry.source,

        slot,

        motionConfig:
          createStickerMotion(
            entry.sticker.motion
              .minScale,

            entry.sticker.motion
              .maxScale,

            entry.sticker.motion
              .rotationRange,

            slot,

            index * 0.34 +
              randomBetween(
                0,
                0.28,
              ),
          ),
      };
    },
  );
}

export function useStickerWorld(
  universalStickers:
    readonly StickerAsset[],

  destinationStickers?:
    readonly StickerAsset[],
) {
  const [
    viewportMode,
    setViewportMode,
  ] =
    useState<ViewportMode>(
      "desktop",
    );

  const viewportModeRef =
    useRef<ViewportMode>(
      "desktop",
    );

  /*
   * Keep SSR and the hydrating client deterministic.
   * Random sticker selection, positions and motion are created
   * only after the component mounts in the browser.
   */
  const [
    activeStickers,
    setActiveStickers,
  ] =
    useState<ActiveSticker[]>(
      [],
    );

  useEffect(() => {
    /*
     * The first server render and first client render both contain
     * an empty sticker layer. Once mounted, initialize the random
     * living world using the real viewport.
     */
    const initialMode =
      getViewportMode(
        window.innerWidth,
      );

    viewportModeRef.current =
      initialMode;

    setViewportMode(
      initialMode,
    );

    setActiveStickers(
      createInitialWorld(
        universalStickers,
        destinationStickers,
        initialMode,
      ),
    );

    const updateViewport =
      () => {
        const nextMode =
          getViewportMode(
            window.innerWidth,
          );

        if (
          viewportModeRef.current ===
          nextMode
        ) {
          return;
        }

        viewportModeRef.current =
          nextMode;

        setViewportMode(
          nextMode,
        );

        setActiveStickers(
          createInitialWorld(
            universalStickers,
            destinationStickers,
            nextMode,
          ),
        );
      };

    window.addEventListener(
      "resize",
      updateViewport,
    );

    return () => {
      window.removeEventListener(
        "resize",
        updateViewport,
      );
    };
  }, [
    universalStickers,
    destinationStickers,
  ]);

  const availableSlots =
    useMemo(
      () =>
        getSlotsForMode(
          viewportMode,
        ),
      [viewportMode],
    );

  const recycleSticker =
    useCallback(
      (
        instanceId: string,
      ) => {
        setActiveStickers(
          (current) => {
            const retiring =
              current.find(
                (entry) =>
                  entry.instanceId ===
                  instanceId,
              );

            if (!retiring) {
              return current;
            }

            const remaining =
              current.filter(
                (entry) =>
                  entry.instanceId !==
                  instanceId,
              );

            /*
             * Destination stickers only replace
             * themselves from destination pool.
             *
             * Universal stickers only replace
             * themselves from universal pool.
             *
             * Result:
             * composition stays exactly 4 + 5.
             */
            const sourcePool =
              retiring.source ===
                "destination" &&
              destinationStickers
                ? destinationStickers
                : universalStickers;

            const activeSameSourceIds =
              new Set(
                remaining
                  .filter(
                    (entry) =>
                      entry.source ===
                      retiring.source,
                  )
                  .map(
                    (entry) =>
                      entry.sticker.id,
                  ),
              );

            /*
             * Prefer:
             * - not currently visible
             * - not the one that just disappeared
             */
            const freshPool =
              sourcePool.filter(
                (sticker) =>
                  !activeSameSourceIds.has(
                    sticker.id,
                  ) &&
                  sticker.id !==
                    retiring.sticker.id,
              );

            const fallbackPool =
              sourcePool.filter(
                (sticker) =>
                  !activeSameSourceIds.has(
                    sticker.id,
                  ),
              );

            const nextSticker =
              shuffle(
                freshPool.length > 0
                  ? freshPool
                  : fallbackPool,
              )[0] ??
              retiring.sticker;

            /*
             * Pick a completely free slot and avoid
             * immediately returning to the slot
             * that was just vacated.
             */
            const occupiedSlotIds =
              new Set(
                remaining.map(
                  (entry) =>
                    entry.slot.id,
                ),
              );

            const freshSlots =
              availableSlots.filter(
                (slot) =>
                  !occupiedSlotIds.has(
                    slot.id,
                  ) &&
                  slot.id !==
                    retiring.slot.id,
              );

            const fallbackSlots =
              availableSlots.filter(
                (slot) =>
                  !occupiedSlotIds.has(
                    slot.id,
                  ),
              );

            const nextSlot =
              shuffle(
                freshSlots.length > 0
                  ? freshSlots
                  : fallbackSlots,
              )[0] ??
              retiring.slot;

            const replacement: ActiveSticker =
              {
                instanceId:
                  createInstanceId(),

                sticker:
                  nextSticker,

                source:
                  retiring.source,

                slot:
                  nextSlot,

                /*
                 * No fixed hero/support/detail.
                 * Same spatial behavior as
                 * Universal Sticker World.
                 */
                motionConfig:
                  createStickerMotion(
                    nextSticker.motion
                      .minScale,

                    nextSticker.motion
                      .maxScale,

                    nextSticker.motion
                      .rotationRange,

                    nextSlot,

                    randomBetween(
                      0.25,
                      0.85,
                    ),
                  ),
              };

            return current.map(
              (entry) =>
                entry.instanceId ===
                instanceId
                  ? replacement
                  : entry,
            );
          },
        );
      },
      [
        universalStickers,
        destinationStickers,
        availableSlots,
      ],
    );

  return {
    activeStickers,
    recycleSticker,
  };
}
