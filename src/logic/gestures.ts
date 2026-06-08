// Pure functions: create the MediaPipe Hands instance and classify gesture state from results

import { HandsConstructor } from '../lib/mediapipe';
import type { Hands, Results } from '../lib/mediapipe';
import type { NormalizedLandmarkList } from '@mediapipe/hands';
import type { GestureType, CropRect } from '../types';

export const initHands = (): Hands => {
  const hands = new HandsConstructor({
    locateFile: (file) =>
      `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
  });

  hands.setOptions({
    maxNumHands: 2,
    modelComplexity: 1,
    minDetectionConfidence: 0.8,
    minTrackingConfidence: 0.5,
  });

  return hands;
};

const dist2D = (
  a: { x: number; y: number },
  b: { x: number; y: number },
): number => Math.hypot(a.x - b.x, a.y - b.y);

// Index finger tip (8) is above its MCP knuckle (5) → finger is extended upward
const isIndexExtended = (lm: NormalizedLandmarkList): boolean =>
  lm[8].y < lm[5].y;

// Thumb tip (4) and index tip (8) are very close → pinch
const isPinching = (lm: NormalizedLandmarkList): boolean =>
  dist2D(lm[4], lm[8]) < 0.06;

// L-shape: index extended and not pinching (thumb + index spread open)
const isFramingHand = (lm: NormalizedLandmarkList): boolean =>
  isIndexExtended(lm) && !isPinching(lm);

export const classifyGesture = (results: Results): GestureType => {
  const hands = results.multiHandLandmarks;
  if (!hands || hands.length < 2) return 'idle';

  const [a, b] = hands;

  if (isPinching(a) && isPinching(b)) return 'pinch';
  if (isFramingHand(a) && isFramingHand(b)) return 'framing';
  return 'idle';
};

// Bounding box of the four fingertips (thumb + index from each hand)
// Returns normalized coords (0–1) matching MediaPipe landmark space
export const getFramingRect = (results: Results): CropRect | null => {
  const hands = results.multiHandLandmarks;
  if (!hands || hands.length < 2) return null;

  const corners = hands.flatMap((lm) => [lm[4], lm[8]]); // thumb tip + index tip
  const xs = corners.map((p) => p.x);
  const ys = corners.map((p) => p.y);

  const x = Math.min(...xs);
  const y = Math.min(...ys);

  return {
    x,
    y,
    width: Math.max(...xs) - x,
    height: Math.max(...ys) - y,
  };
};
