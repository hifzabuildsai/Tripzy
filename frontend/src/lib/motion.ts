export type StickerDepth = "far" | "mid" | "near";
export type StickerSlot = {
  id: string;
  x: [number, number];
  y: [number, number];
  depth: StickerDepth;
  drift: [number, number];
};

export type StickerMotionConfig = {
  depth: StickerDepth;
  startX: number;
  startY: number;
  driftX: number;
  driftY: number;
  startScale: number;
  endScale: number;
  startRotation: number;
  endRotation: number;
  duration: number;
  delay: number;
  maxOpacity: number;
};

const slot = (id: string, x: [number, number], y: [number, number], depth: StickerDepth, drift: [number, number]): StickerSlot => ({ id, x, y, depth, drift });

export const MOBILE_STICKER_SLOTS = [
  slot("m-top-left", [8, 20], [8, 20], "mid", [5, 8]),
  slot("m-top-right", [78, 91], [10, 23], "far", [-5, 7]),
  slot("m-bottom-left", [7, 20], [78, 91], "far", [5, -8]),
  slot("m-bottom-right", [79, 92], [75, 89], "mid", [-6, -7]),
];

export const TABLET_STICKER_SLOTS = [
  slot("t-top-left", [7, 19], [8, 20], "mid", [7, 8]),
  slot("t-top-mid", [37, 48], [5, 16], "far", [-4, 8]),
  slot("t-top-right", [80, 91], [10, 23], "near", [-7, 7]),
  slot("t-mid-left", [5, 16], [43, 58], "far", [7, -3]),
  slot("t-mid-right", [84, 94], [43, 58], "mid", [-7, 3]),
  slot("t-bottom-left", [10, 23], [79, 90], "near", [5, -8]),
  slot("t-bottom-right", [75, 89], [78, 91], "far", [-6, -7]),
];

export const DESKTOP_STICKER_SLOTS = [
  slot("d-top-left", [5, 14], [7, 18], "near", [7, 8]),
  slot("d-top-left-inner", [23, 33], [4, 14], "far", [-4, 7]),
  slot("d-top-right-inner", [68, 78], [5, 16], "mid", [4, 7]),
  slot("d-top-right", [87, 95], [8, 20], "near", [-8, 8]),
  slot("d-mid-left", [4, 12], [43, 56], "far", [7, -2]),
  slot("d-mid-right", [88, 96], [40, 55], "mid", [-8, 3]),
  slot("d-bottom-left", [5, 15], [79, 91], "mid", [7, -8]),
  slot("d-bottom-left-inner", [24, 35], [84, 94], "far", [-4, -7]),
  slot("d-bottom-right-inner", [67, 78], [83, 94], "near", [5, -8]),
  slot("d-bottom-right", [87, 96], [77, 90], "far", [-7, -7]),
  slot("d-upper-left", [12, 22], [26, 36], "far", [5, 5]),
  slot("d-lower-right", [79, 88], [63, 75], "mid", [-5, -5]),
];

function random(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

export function createStickerMotion(minScale: number, maxScale: number, rotationRange: number, stickerSlot: StickerSlot, delay: number): StickerMotionConfig {
  const startScale = random(minScale, maxScale);
  return {
    depth: stickerSlot.depth,
    startX: random(...stickerSlot.x),
    startY: random(...stickerSlot.y),
    driftX: random(-stickerSlot.drift[0], stickerSlot.drift[0]),
    driftY: random(-stickerSlot.drift[1], stickerSlot.drift[1]),
    startScale,
    endScale: startScale * random(0.96, 1.06),
    startRotation: random(-rotationRange, rotationRange),
    endRotation: random(-rotationRange, rotationRange),
    duration: random(18, 27),
    delay,
    maxOpacity: stickerSlot.depth === "far" ? 0.7 : stickerSlot.depth === "mid" ? 0.84 : 0.94,
  };
}
