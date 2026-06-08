// Component: renders the fullscreen video feed with a transparent overlay canvas stacked on top

import { useRef } from 'react';
import { useCamera } from '../hooks/useCamera';
import { useGestures } from '../hooks/useGestures';

export const CameraView = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { error } = useCamera(videoRef, canvasRef);
  useGestures(videoRef, canvasRef);

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
