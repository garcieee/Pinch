// Shared TypeScript types for the entire app

export type GestureType = 'idle' | 'framing' | 'pinch';

// Normalized coordinates (0–1) matching MediaPipe landmark space
export type CropRect = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type Card = {
  id: string;
  imageUrl: string;
  x: number;
  y: number;
};

export type AppState = {
  gesture: GestureType;
  cards: Card[];
};
