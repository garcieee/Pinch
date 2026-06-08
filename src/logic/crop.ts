// Pure function: extracts a crop region from a live video element and returns an object URL

import type { CropRect } from '../types';

export const extractCrop = (video: HTMLVideoElement, rect: CropRect): Promise<string> => {
  const { videoWidth, videoHeight } = video;

  // rect is in normalized coords (0–1) — convert to native video pixels
  const sx = rect.x * videoWidth;
  const sy = rect.y * videoHeight;
  const sw = rect.width * videoWidth;
  const sh = rect.height * videoHeight;

  const canvas = document.createElement('canvas');
  canvas.width = sw;
  canvas.height = sh;

  const ctx = canvas.getContext('2d');
  if (!ctx) return Promise.reject(new Error('No 2D context'));

  ctx.drawImage(video, sx, sy, sw, sh, 0, 0, sw, sh);

  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) { reject(new Error('Blob creation failed')); return; }
      resolve(URL.createObjectURL(blob));
    }, 'image/png');
  });
};
