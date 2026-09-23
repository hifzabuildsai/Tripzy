import FloatingSticker from "@/components/stickers/FloatingSticker";

import type { ActiveSticker } from "@/hooks/useStickerWorld";

type StickerLayerProps = {
  stickers: ActiveSticker[];
  onRecycleSticker: (instanceId: string) => void;
};

export default function StickerLayer({
  stickers,
  onRecycleSticker,
}: StickerLayerProps) {
  return (
    <>
      {stickers.map(
        ({
          instanceId,
          sticker,
          motionConfig,
        }) => (
          <FloatingSticker
            key={instanceId}
            sticker={sticker}
            motionConfig={motionConfig}
            onCycleComplete={() =>
              onRecycleSticker(instanceId)
            }
          />
        ),
      )}
    </>
  );
}