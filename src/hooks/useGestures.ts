// Hook: runs MediaPipe Hands per frame, draws landmarks + framing rect, fires onSnap on pinch

import { useEffect, useRef } from 'react';
import type { RefObject } from 'react';
import {
  CameraConstructor,
  drawConnectors,
  drawLandmarks,
  HAND_CONNECTIONS,
} from '../lib/mediapipe';
import type { Results } from '../lib/mediapipe';
import { initHands, classifyGesture, getFramingRect } from '../logic/gestures';
import type { CropRect, GestureType } from '../types';

const drawHandLandmarks = (canvas: HTMLCanvasElement, results: Results): void => {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!results.multiHandLandmarks?.length) return;

  for (const landmarks of results.multiHandLandmarks) {
    drawConnectors(ctx, landmarks, HAND_CONNECTIONS, { color: '#00FF00', lineWidth: 2 });
    drawLandmarks(ctx, landmarks, {
      color: '#FF0000',
      fillColor: '#FF000066',
      lineWidth: 1,
      radius: 4,
    });
  }
};

const drawFramingRect = (canvas: HTMLCanvasElement, rect: CropRect): void => {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.save();
  ctx.strokeStyle = '#3B82F6';
  ctx.lineWidth = 3;
  ctx.setLineDash([12, 6]);
  ctx.strokeRect(
    rect.x * canvas.width,
    rect.y * canvas.height,
    rect.width * canvas.width,
    rect.height * canvas.height,
  );
  ctx.restore();
};

export const useGestures = (
  videoRef: RefObject<HTMLVideoElement | null>,
  canvasRef: RefObject<HTMLCanvasElement | null>,
  onSnap: (rect: CropRect) => void,
) => {
  // Keep onSnap stable across renders without restarting the MediaPipe loop
  const onSnapRef = useRef(onSnap);
  useEffect(() => { onSnapRef.current = onSnap; });

  const cameraRef = useRef<{ start(): Promise<void>; stop(): Promise<void> } | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const hands = initHands();

    // State machine lives here — transitions tracked per-frame inside the closure
    let prevGesture: GestureType = 'idle';
    let savedRect: CropRect | null = null;

    hands.onResults((results: Results) => {
      const gesture = classifyGesture(results);

      drawHandLandmarks(canvas, results);

      if (gesture === 'framing') {
        const rect = getFramingRect(results);
        if (rect) {
          savedRect = rect;
          drawFramingRect(canvas, rect);
        }
      }

      // Edge: framing → pinch fires snap exactly once
      if (prevGesture === 'framing' && gesture === 'pinch' && savedRect) {
        onSnapRef.current(savedRect);
        savedRect = null;
      }

      if (gesture === 'idle') savedRect = null;

      prevGesture = gesture;
    });

    const camera = new CameraConstructor(video, {
      onFrame: async () => {
        await hands.send({ image: video });
      },
    });

    cameraRef.current = camera;
    camera.start();

    return () => {
      camera.stop();
      hands.close();
      cameraRef.current = null;
    };
  }, [videoRef, canvasRef]);
};
