"use client";

import StickerLayer from "@/components/stickers/StickerLayer";

import { universalStickers } from "@/data/stickers/universal";
import { useStickerWorld } from "@/hooks/useStickerWorld";

export default function StickerWorld() {
  const {
    activeStickers,
    recycleSticker,
  } = useStickerWorld(
    universalStickers,
  );

  return (
    <div
      className="pointer-events-none absolute inset-0 z-0 overflow-hidden"
      aria-hidden="true"
    >
      <StickerLayer
        stickers={activeStickers}
        onRecycleSticker={
          recycleSticker
        }
      />
    </div>
  );
}