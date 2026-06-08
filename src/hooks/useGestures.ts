// Hook: runs MediaPipe Hands on each camera frame and draws live landmarks on the overlay canvas

import { useState, useEffect, useRef } from 'react';
import type { RefObject } from 'react';
import {
  CameraConstructor,
  drawConnectors,
  drawLandmarks,
  HAND_CONNECTIONS,
} from '../lib/mediapipe';
import type { Results } from '../lib/mediapipe';
import { initHands, classifyGesture } from '../logic/gestures';
import type { GestureType } from '../types';

const drawHandLandmarks = (canvas: HTMLCanvasElement, results: Results): void => {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!results.multiHandLandmarks?.length) return;

  for (const landmarks of results.multiHandLandmarks) {
    drawConnectors(ctx, landmarks, HAND_CONNECTIONS, {
      color: '#00FF00',
      lineWidth: 2,
    });
    drawLandmarks(ctx, landmarks, {
      color: '#FF0000',
      fillColor: '#FF000066',
      lineWidth: 1,
      radius: 4,
    });
  }
};

export const useGestures = (
  videoRef: RefObject<HTMLVideoElement | null>,
  canvasRef: RefObject<HTMLCanvasElement | null>,
) => {
  const [gestureType, setGestureType] = useState<GestureType>('idle');
  const cameraRef = useRef<{ start(): Promise<void>; stop(): Promise<void> } | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const hands = initHands();

    hands.onResults((results: Results) => {
      drawHandLandmarks(canvas, results);
      setGestureType(classifyGesture(results));
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

  return { gestureType };
};
