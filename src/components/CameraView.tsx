// Component: renders the fullscreen video feed with a transparent overlay canvas stacked on top

import { useRef, useState, useCallback } from 'react';
import { useCamera } from '../hooks/useCamera';
import { useGestures } from '../hooks/useGestures';
import { useAppState } from '../hooks/useAppState';
import { extractCrop } from '../logic/crop';
import type { CropRect } from '../types';

export const CameraView = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const { state, dispatch } = useAppState();
  const { error } = useCamera(videoRef, canvasRef);

  const [flashKey, setFlashKey] = useState(0);
  const [flashing, setFlashing] = useState(false);

  const triggerFlash = useCallback(() => {
    setFlashing(false);
    // Force animation restart by cycling key + re-enabling class next tick
    setFlashKey((k) => k + 1);
    requestAnimationFrame(() => setFlashing(true));
  }, []);

  const onSnap = useCallback(
    (rect: CropRect) => {
      const video = videoRef.current;
      if (!video) return;

      extractCrop(video, rect)
        .then((imageUrl) => {
          const card = {
            id: crypto.randomUUID(),
            imageUrl,
            x: Math.random() * 200 + 40,
            y: Math.random() * 200 + 40,
          };
          console.log('[Pinch] Card added to state:', card);
          dispatch({ type: 'ADD_CARD', card });
          triggerFlash();
        })
        .catch((err) => console.error('[Pinch] Crop failed:', err));
    },
    [dispatch, triggerFlash],
  );

  useGestures(videoRef, canvasRef, onSnap);

  // Log state on every card change so it's visible during testing
  console.log('[AppState] cards:', state.cards.length, state.cards);

  return (
    <div className="camera-root">
      <video
        ref={videoRef}
        className="camera-video"
        autoPlay
        playsInline
        muted
      />
      <canvas ref={canvasRef} className="camera-overlay" />
      <div
        key={flashKey}
        className={`shutter-flash${flashing ? ' active' : ''}`}
      />
      {error && <div className="camera-error">Camera error: {error}</div>}
    </div>
  );
};
