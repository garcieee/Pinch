// Pure functions: create the MediaPipe Hands instance and classify gesture state from results

import { HandsConstructor } from '../lib/mediapipe';
import type { Hands, Results } from '../lib/mediapipe';
import type { GestureType } from '../types';

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

// Stub — real classification (framing / pinch detection) is implemented in Phase 4
export const classifyGesture = (_results: Results): GestureType => 'idle';
