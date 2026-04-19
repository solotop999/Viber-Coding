import { useEffect, useState, type RefObject } from "react";

type CameraState = {
  isReady: boolean;
  error: string | null;
};

export function useCamera(videoRef: RefObject<HTMLVideoElement | null>, enabled: boolean) {
  const [state, setState] = useState<CameraState>({ isReady: false, error: null });

  useEffect(() => {
    if (!enabled) {
      setState({ isReady: false, error: null });
      return;
    }

    let activeStream: MediaStream | null = null;
    let cancelled = false;

    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: false,
          video: {
            facingMode: "user",
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
        });

        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        activeStream = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setState({ isReady: true, error: null });
      } catch {
        setState({
          isReady: false,
          error: "Unable to access camera. Check permissions and try again.",
        });
      }
    }

    void startCamera();

    return () => {
      cancelled = true;
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      activeStream?.getTracks().forEach((track) => track.stop());
    };
  }, [enabled, videoRef]);

  return state;
}
