"use client";

import StickerLayer from "@/components/stickers/StickerLayer";

import { universalStickers } from "@/data/stickers/universal";
import { useStickerWorld } from "@/hooks/useStickerWorld";

import type { StickerAsset } from "@/types/sticker";

type StickerWorldProps = {
  destinationStickers?:
    readonly StickerAsset[];
};

export default function StickerWorld({
  destinationStickers,
}: StickerWorldProps) {
  const {
    activeStickers,
    recycleSticker,
  } = useStickerWorld(
    universalStickers,
    destinationStickers,
  );

  return (
    <div
      className="pointer-events-none absolute inset-0 overflow-hidden"
      aria-hidden="true"
    >
      <StickerLayer
        stickers={
          activeStickers
        }
        onRecycleSticker={
          recycleSticker
        }
      />
    </div>
  );
}