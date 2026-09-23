"use client";

import {
  useCallback,
  useEffect,
  useMemo,
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

export type ActiveSticker = {
  instanceId: string;
  sticker: StickerAsset;
  slot: StickerSlot;
  motionConfig: StickerMotionConfig;
};

type ViewportMode =
  | "mobile"
  | "tablet"
  | "laptop"
  | "desktop";

function shuffle<T>(items: readonly T[]): T[] {
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

function getStickerCount(
  mode: ViewportMode,
): number {
  if (mode === "mobile") {
    return 4;
  }

  if (mode === "tablet") {
    return 6;
  }

  if (mode === "laptop") {
    return 8;
  }

  return 9;
}

function createInstanceId(): string {
  return `${Date.now()}-${Math.random()
    .toString(36)
    .slice(2)}`;
}

function createInitialWorld(
  stickers: readonly StickerAsset[],
  mode: ViewportMode,
): ActiveSticker[] {
  const count = getStickerCount(mode);

  const selectedStickers = shuffle(
    stickers,
  ).slice(
    0,
    Math.min(count, stickers.length),
  );

  const selectedSlots = shuffle(
    getSlotsForMode(mode),
  ).slice(0, selectedStickers.length);

  return selectedStickers.map(
    (sticker, index) => {
      const slot = selectedSlots[index];

      /*
       * Small initial stagger means the whole world
       * doesn't enter/leave at the exact same moment.
       */
      const entranceDelay =
        index * 0.42 +
        randomBetween(0, 0.3);

      return {
        instanceId: createInstanceId(),

        sticker,

        slot,

        motionConfig: createStickerMotion(
          sticker.motion.minScale,
          sticker.motion.maxScale,
          sticker.motion.rotationRange,
          slot,
          entranceDelay,
        ),
      };
    },
  );
}

export function useStickerWorld(
  stickers: readonly StickerAsset[],
) {
  const [viewportMode, setViewportMode] =
    useState<ViewportMode>("desktop");

  const [activeStickers, setActiveStickers] =
    useState<ActiveSticker[]>([]);

  useEffect(() => {
    const updateViewport = () => {
      const nextMode = getViewportMode(
        window.innerWidth,
      );

      setViewportMode((currentMode) =>
        currentMode === nextMode
          ? currentMode
          : nextMode,
      );
    };

    updateViewport();

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
  }, []);

  useEffect(() => {
    setActiveStickers(
      createInitialWorld(
        stickers,
        viewportMode,
      ),
    );
  }, [stickers, viewportMode]);

  const availableWorldSlots = useMemo(
    () => getSlotsForMode(viewportMode),
    [viewportMode],
  );

  const recycleSticker = useCallback(
    (instanceId: string) => {
      setActiveStickers((current) => {
        const retiringSticker =
          current.find(
            (entry) =>
              entry.instanceId ===
              instanceId,
          );

        if (!retiringSticker) {
          return current;
        }

        const remaining = current.filter(
          (entry) =>
            entry.instanceId !==
            instanceId,
        );

        /*
         * Don't immediately repeat the sticker that
         * just disappeared, and don't duplicate any
         * sticker currently visible.
         */
        const activeStickerIds = new Set(
          remaining.map(
            (entry) => entry.sticker.id,
          ),
        );

        const freshStickerPool =
          stickers.filter(
            (sticker) =>
              !activeStickerIds.has(
                sticker.id,
              ) &&
              sticker.id !==
                retiringSticker.sticker.id,
          );

        const nextSticker =
          shuffle(
            freshStickerPool.length > 0
              ? freshStickerPool
              : stickers,
          )[0];

        /*
         * New sticker must also move somewhere else.
         */
        const occupiedSlotIds = new Set(
          remaining.map(
            (entry) => entry.slot.id,
          ),
        );

        const freshSlotPool =
          availableWorldSlots.filter(
            (slot) =>
              !occupiedSlotIds.has(
                slot.id,
              ) &&
              slot.id !==
                retiringSticker.slot.id,
          );

        const fallbackSlotPool =
          availableWorldSlots.filter(
            (slot) =>
              !occupiedSlotIds.has(
                slot.id,
              ),
          );

        const nextSlot =
          shuffle(
            freshSlotPool.length > 0
              ? freshSlotPool
              : fallbackSlotPool,
          )[0] ?? retiringSticker.slot;

        const replacement: ActiveSticker = {
          instanceId: createInstanceId(),

          sticker: nextSticker,

          slot: nextSlot,

          motionConfig: createStickerMotion(
            nextSticker.motion.minScale,
            nextSticker.motion.maxScale,
            nextSticker.motion.rotationRange,
            nextSlot,
            randomBetween(0.25, 0.9),
          ),
        };

        return current.map((entry) =>
          entry.instanceId ===
          instanceId
            ? replacement
            : entry,
        );
      });
    },
    [stickers, availableWorldSlots],
  );

  return {
    activeStickers,
    recycleSticker,
  };
}