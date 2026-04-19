import { useEffect, useRef, type RefObject } from "react";
import { PoseLandmarker, type NormalizedLandmark } from "@mediapipe/tasks-vision";

type CameraPreviewProps = {
  videoRef: RefObject<HTMLVideoElement | null>;
  poseLandmarks: NormalizedLandmark[];
  showSkeleton: boolean;
  mirror?: boolean;
  hideVideo?: boolean;
  showChrome?: boolean;
};

function connectionAlpha(start: NormalizedLandmark, end: NormalizedLandmark) {
  const startVisibility = start.visibility ?? 0;
  const endVisibility = end.visibility ?? 0;
  return Math.max(0.2, Math.min(1, (startVisibility + endVisibility) / 2));
}

function pointColor(visibility: number) {
  if (visibility >= 0.75) {
    return "rgba(115, 255, 168, 0.98)";
  }
  if (visibility >= 0.5) {
    return "rgba(255, 209, 102, 0.95)";
  }
  return "rgba(255, 122, 37, 0.9)";
}

function drawSkeleton(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  landmarks: NormalizedLandmark[],
) {
  ctx.clearRect(0, 0, width, height);

  if (!landmarks.length) {
    return;
  }

  ctx.save();
  ctx.translate(width, 0);
  ctx.scale(-1, 1);

  ctx.lineWidth = 3;

  for (const connection of PoseLandmarker.POSE_CONNECTIONS) {
    const start = landmarks[connection.start];
    const end = landmarks[connection.end];

    if (!start || !end) {
      continue;
    }

    const alpha = connectionAlpha(start, end);
    ctx.strokeStyle = `rgba(255, 122, 37, ${alpha})`;
    ctx.beginPath();
    ctx.moveTo(start.x * width, start.y * height);
    ctx.lineTo(end.x * width, end.y * height);
    ctx.stroke();
  }

  for (const landmark of landmarks) {
    const visibility = landmark.visibility ?? 0;
    if (visibility < 0.35) {
      continue;
    }

    ctx.fillStyle = pointColor(visibility);
    ctx.beginPath();
    ctx.arc(landmark.x * width, landmark.y * height, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.restore();
}

export default function CameraPreview({
  videoRef,
  poseLandmarks,
  showSkeleton,
  mirror = true,
  hideVideo = false,
  showChrome = true,
}: CameraPreviewProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height) {
      return;
    }

    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }

    if (!showSkeleton) {
      ctx.clearRect(0, 0, width, height);
      return;
    }

    if (mirror) {
      drawSkeleton(ctx, width, height, poseLandmarks);
      return;
    }

    ctx.clearRect(0, 0, width, height);
    ctx.lineWidth = 3;

    for (const connection of PoseLandmarker.POSE_CONNECTIONS) {
      const start = poseLandmarks[connection.start];
      const end = poseLandmarks[connection.end];

      if (!start || !end) {
        continue;
      }

      const alpha = connectionAlpha(start, end);
      ctx.strokeStyle = `rgba(255, 122, 37, ${alpha})`;
      ctx.beginPath();
      ctx.moveTo(start.x * width, start.y * height);
      ctx.lineTo(end.x * width, end.y * height);
      ctx.stroke();
    }

    for (const landmark of poseLandmarks) {
      const visibility = landmark.visibility ?? 0;
      if (visibility < 0.35) {
        continue;
      }

      ctx.fillStyle = pointColor(visibility);
      ctx.beginPath();
      ctx.arc(landmark.x * width, landmark.y * height, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [mirror, poseLandmarks, showSkeleton]);

  return (
    <div className={`absolute inset-0 overflow-hidden ${hideVideo ? "bg-transparent" : "bg-black"}`}>
      {!hideVideo ? (
        <video
          ref={videoRef}
          className={`h-full w-full object-cover ${mirror ? "scale-x-[-1]" : ""}`}
          autoPlay
          muted
          playsInline
        />
      ) : null}
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
      {showChrome ? (
        <>
          <div className="pointer-events-none absolute inset-x-[14%] top-[18%] bottom-[22%] rounded-[36px] border border-white/12">
            <div className="absolute left-1/2 top-[14%] h-[1px] w-[44%] -translate-x-1/2 bg-white/16" />
            <div className="absolute left-1/2 bottom-[18%] h-[1px] w-[52%] -translate-x-1/2 bg-white/14" />
          </div>
          <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(3,3,4,0.75)_0%,rgba(3,3,4,0.05)_30%,rgba(3,3,4,0.2)_60%,rgba(3,3,4,0.82)_100%)]" />
        </>
      ) : null}
    </div>
  );
}
