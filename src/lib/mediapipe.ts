// Shim: exposes MediaPipe CDN globals as typed ES module exports.
// The actual JS is loaded via <script> tags in index.html (IIFE bundles that attach to window).
// npm packages (@mediapipe/*) are kept only for TypeScript type definitions.

import type { Hands, Results, LandmarkConnectionArray } from '@mediapipe/hands';
import type { Camera, CameraOptions } from '@mediapipe/camera_utils';
import type {
  drawConnectors as DrawConnectorsFn,
  drawLandmarks as DrawLandmarksFn,
  DrawingOptions,
} from '@mediapipe/drawing_utils';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;

export const HandsConstructor = g.Hands as {
  new (config?: { locateFile?: (file: string) => string }): Hands;
};

export const CameraConstructor = g.Camera as {
  new (video: HTMLVideoElement, options: CameraOptions): Camera;
};

export const drawConnectors: typeof DrawConnectorsFn = g.drawConnectors;
export const drawLandmarks: typeof DrawLandmarksFn = g.drawLandmarks;
export const HAND_CONNECTIONS: LandmarkConnectionArray = g.HAND_CONNECTIONS;

export type { Hands, Results, LandmarkConnectionArray, CameraOptions, DrawingOptions };
