"use client";

import {
  AnimatePresence,
  motion,
} from "motion/react";

import StickerWorld from "@/components/stickers/StickerWorld";

import {
  resolveStickerWorld,
  type StickerWorldId,
} from "@/data/stickers/registry";

type DestinationTransitionProps = {
  destination?: string;
};

function getAtmosphere(
  worldId: StickerWorldId,
): string {
  if (worldId === "seoul") {
    return [
      "radial-gradient(circle at 15% 20%, rgba(244, 194, 205, 0.14), transparent 34%)",
      "radial-gradient(circle at 86% 24%, rgba(183, 211, 224, 0.13), transparent 35%)",
      "radial-gradient(circle at 75% 85%, rgba(240, 207, 216, 0.10), transparent 34%)",
    ].join(", ");
  }

  if (worldId === "istanbul") {
    return [
      "radial-gradient(circle at 15% 22%, rgba(211, 145, 96, 0.12), transparent 34%)",
      "radial-gradient(circle at 86% 25%, rgba(221, 182, 126, 0.12), transparent 35%)",
      "radial-gradient(circle at 74% 85%, rgba(181, 116, 78, 0.08), transparent 34%)",
    ].join(", ");
  }

  return "none";
}

export default function DestinationTransition({
  destination,
}: DestinationTransitionProps) {
  const world =
    resolveStickerWorld(
      destination,
    );

  const hasDestination =
    world.id !== "universal";

  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <AnimatePresence
        initial={false}
        mode="sync"
      >
        <motion.div
          key={world.id}
          className="pointer-events-none absolute inset-0"
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          exit={{
            opacity: 0,
          }}
          transition={{
            duration: 1.8,
            ease: [
              0.22,
              1,
              0.36,
              1,
            ],
          }}
        >
          <div
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                getAtmosphere(
                  world.id,
                ),
            }}
          />

          <motion.div
            className="pointer-events-none absolute inset-0"
            initial={{
              opacity: 0,
              scale: 0.985,
              filter:
                "blur(8px)",
            }}
            animate={{
              opacity: 1,
              scale: 1,
              filter:
                "blur(0px)",
            }}
            exit={{
              opacity: 0,
              scale: 1.025,
              filter:
                "blur(10px)",
            }}
            transition={{
              duration: 1.6,
              ease: [
                0.22,
                1,
                0.36,
                1,
              ],
            }}
          >
            <StickerWorld
              destinationStickers={
                hasDestination
                  ? world.stickers
                  : undefined
              }
            />
          </motion.div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}