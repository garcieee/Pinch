// Component: renders the fullscreen video feed with a transparent overlay canvas stacked on top

import { useRef, useEffect } from 'react';
import { useCamera } from '../hooks/useCamera';

export const CameraView = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { ready, error } = useCamera(videoRef, canvasRef);

  // TEST OVERLAY — remove once canvas alignment is confirmed
  useEffect(() => {
    if (!ready || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 6;
    ctx.strokeRect(cx - 150, cy - 100, 300, 200);
  }, [ready]);

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
      {error && <div className="camera-error">Camera error: {error}</div>}
    </div>
  );
};
