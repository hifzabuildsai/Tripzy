import { istanbulStickers } from "@/data/stickers/istanbul";
import { southKoreaStickers } from "@/data/stickers/south-korea";
import { universalStickers } from "@/data/stickers/universal";

import type { StickerAsset } from "@/types/sticker";

export type StickerWorldId =
  | "universal"
  | "seoul"
  | "istanbul";

export type StickerWorldSelection = {
  id: StickerWorldId;

  label: string;

  stickers:
    readonly StickerAsset[];
};

export function resolveStickerWorld(
  destination?: string,
): StickerWorldSelection {
  const normalized =
    destination
      ?.trim()
      .toLowerCase() ?? "";

  if (
    normalized.includes(
      "seoul",
    ) ||
    normalized.includes(
      "south korea",
    ) ||
    normalized === "korea"
  ) {
    return {
      id: "seoul",
      label: "Seoul",
      stickers:
        southKoreaStickers,
    };
  }

  if (
    normalized.includes(
      "istanbul",
    ) ||
    normalized.includes(
      "turkey",
    ) ||
    normalized.includes(
      "turkiye",
    ) ||
    normalized.includes(
      "türkiye",
    )
  ) {
    return {
      id: "istanbul",
      label: "Istanbul",
      stickers:
        istanbulStickers,
    };
  }

  return {
    id: "universal",
    label: "Travel",
    stickers:
      universalStickers,
  };
}