export type StickerCategory =
  | "travel"
  | "landmark"
  | "food"
  | "drink"
  | "culture"
  | "transport"
  | "nature"
  | "map"
  | "symbol"
  | "architecture"
  | "ephemera"
  | "local-object";

export type StickerAsset = {
  id: string;

  name: string;
  category: StickerCategory;

  assetPath: string;

  destination?: string;
  country?: string;

  tags: string[];

  aspectRatio: number;

  motion: {
    weight: number;
    minScale: number;
    maxScale: number;
    rotationRange: number;
  };

  accessibility: {
    alt: string;
    decorative: boolean;
  };
};