// Shared TypeScript types for the entire app

export type GestureType = 'idle' | 'framing' | 'pinch';

export type AppState = {
  gesture: GestureType;
};
