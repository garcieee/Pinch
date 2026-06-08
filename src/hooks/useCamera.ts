// Hook: initializes the webcam on mount, sizes the canvas to match video, tracks ready/error state

import { useState, useEffect } from 'react';
import type { RefObject } from 'react';
import { startCamera } from '../logic/camera';

export const useCamera = (
  videoRef: RefObject<HTMLVideoElement | null>,
  canvasRef: RefObject<HTMLCanvasElement | null>,
) => {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!videoRef.current) return;

    startCamera(videoRef.current)
      .then(() => {
        const video = videoRef.current!;
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
        }
        setReady(true);
      })
      .catch((err: Error) => {
        console.error('[useCamera] Failed to start camera:', err);
        setError(err.message);
      });
  }, [videoRef, canvasRef]);

  return { ready, error };
};
