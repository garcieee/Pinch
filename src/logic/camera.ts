// Pure function: requests webcam access and attaches the stream to a video element

export const startCamera = async (videoEl: HTMLVideoElement): Promise<void> => {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  videoEl.srcObject = stream;
  return new Promise((resolve) => {
    videoEl.onloadedmetadata = () => {
      videoEl.play();
      resolve();
    };
  });
};
