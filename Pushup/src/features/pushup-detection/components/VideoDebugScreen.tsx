import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import type { NormalizedLandmark } from "@mediapipe/tasks-vision";
import CameraPreview from "./CameraPreview";
import DebugStrip from "./DebugStrip";
import SessionGuide from "./SessionGuide";
import SessionHud from "./SessionHud";
import { loadPoseLandmarker } from "../lib/mediapipeLoader";
import { PushupDetector } from "../lib/pushupDetector";
import { DETECTION_INTERVAL_MS } from "../model/constants";
import type { DetectorFrameState, DetectorStatus } from "../model/detectorTypes";

type VideoDebugScreenProps = {
  onClose: () => void;
};

const initialFrame: DetectorFrameState = {
  status: "idle",
  phase: "unknown",
  repCount: 0,
  confidence: 0,
  fps: 0,
  calibrationProgress: 0,
  baseline: null,
  upThreshold: null,
  downThreshold: null,
  message: "Chọn video để debug",
  debug: {
    active: false,
    rawHeadHeight: null,
    smoothedHeadHeight: null,
    rawMotionSignal: null,
    smoothedMotionSignal: null,
    rawElbowAngle: null,
    smoothedElbowAngle: null,
    transitionFrom: "unknown",
    transitionTo: "unknown",
    transitionCompletedRep: false,
    reachedBottom: false,
    elapsedMsSinceLastRep: null,
    minRepDurationMs: null,
    maxRepDurationMs: null,
    activationRange: null,
    oscillationRange: 0,
    bufferFill: 0,
    repBlockReason: "none",
  },
};

const DEFAULT_DEBUG_VIDEO_URL = "/vidu.mp4";
const DEFAULT_DEBUG_VIDEO_NAME = "vidu.mp4";

export default function VideoDebugScreen({ onClose }: VideoDebugScreenProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const requestRef = useRef<number | null>(null);
  const detectorRef = useRef<PushupDetector | null>(null);
  const poseLandmarkerRef = useRef<Awaited<ReturnType<typeof loadPoseLandmarker>> | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const lastProcessedTimeRef = useRef(-1);

  const [poseLandmarks, setPoseLandmarks] = useState<NormalizedLandmark[]>([]);
  const [frame, setFrame] = useState<DetectorFrameState>(initialFrame);
  const [status, setStatus] = useState<DetectorStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [videoFileName, setVideoFileName] = useState("");
  const [elapsedSec, setElapsedSec] = useState(0);

  const isVideoSelected = Boolean(videoFileName);

  useEffect(() => {
    let cancelled = false;

    async function prepare() {
      try {
        const poseLandmarker = await loadPoseLandmarker();
        if (cancelled) {
          return;
        }

        poseLandmarkerRef.current = poseLandmarker;
        detectorRef.current = new PushupDetector(navigator.userAgent);
      } catch {
        if (cancelled) {
          return;
        }

        setStatus("error");
        setError("Không tải được bộ nhận diện cho chế độ debug video.");
      }
    }

    void prepare();

    return () => {
      cancelled = true;
      if (requestRef.current !== null) {
        cancelAnimationFrame(requestRef.current);
      }
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const video = videoRef.current;

    if (!video || isVideoSelected) {
      return;
    }

    video.src = DEFAULT_DEBUG_VIDEO_URL;
    video.load();
    setVideoFileName(DEFAULT_DEBUG_VIDEO_NAME);
    resetDebugState("Đã nạp video mẫu, bấm phát để debug");
  }, [isVideoSelected]);

  useEffect(() => {
    const tick = () => {
      const video = videoRef.current;
      const poseLandmarker = poseLandmarkerRef.current;
      const detector = detectorRef.current;

      if (!video || !poseLandmarker || !detector) {
        requestRef.current = requestAnimationFrame(tick);
        return;
      }

      if (video.paused || video.ended || video.readyState < 2) {
        requestRef.current = requestAnimationFrame(tick);
        return;
      }

      const timestampMs = video.currentTime * 1000;
      if (timestampMs - lastProcessedTimeRef.current < DETECTION_INTERVAL_MS) {
        requestRef.current = requestAnimationFrame(tick);
        return;
      }

      lastProcessedTimeRef.current = timestampMs;
      const result = poseLandmarker.detectForVideo(video, timestampMs);
      const nextFrame = detector.process(result, timestampMs);

      setFrame(nextFrame);
      setStatus(nextFrame.status);
      setPoseLandmarks(result.landmarks[0] ?? []);
      setElapsedSec(Math.floor(video.currentTime));

      requestRef.current = requestAnimationFrame(tick);
    };

    requestRef.current = requestAnimationFrame(tick);

    return () => {
      if (requestRef.current !== null) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, []);

  function resetDebugState(message: string) {
    detectorRef.current?.reset();
    lastProcessedTimeRef.current = -1;
    setPoseLandmarks([]);
    setElapsedSec(0);
    setStatus("idle");
    setError(null);
    setFrame({ ...initialFrame, message });
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    const video = videoRef.current;

    if (!file || !video) {
      return;
    }

    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
    }

    const objectUrl = URL.createObjectURL(file);
    objectUrlRef.current = objectUrl;
    video.src = objectUrl;
    video.load();
    setVideoFileName(file.name);
    resetDebugState("Nhấn phát video để bắt đầu debug");
  }

  function handleLoadedMetadata() {
    resetDebugState("Video sẵn sàng, bấm phát để chạy detection");
  }

  function handlePlay() {
    setStatus((current) => (current === "idle" ? "tracking" : current));
    setError(null);
  }

  function handlePause() {
    if (videoRef.current?.ended) {
      setStatus("finished");
      setFrame((current) => ({ ...current, status: "finished", message: "Video đã chạy xong" }));
      return;
    }

    setStatus("paused");
    setFrame((current) => ({ ...current, status: "paused", message: "Video đang tạm dừng" }));
  }

  function handleEnded() {
    setStatus("finished");
    setFrame((current) => ({ ...current, status: "finished", message: "Video đã chạy xong" }));
  }

  const helperMessage = useMemo(() => {
    if (error) {
      return error;
    }

    if (!isVideoSelected) {
      return "Chọn video hít đất để xem pose và detector chạy trên từng frame.";
    }

    return frame.message;
  }, [error, frame.message, isVideoSelected]);

  return (
    <div className="relative h-full min-h-screen overflow-hidden bg-black text-white">
      <video
        ref={videoRef}
        className="absolute inset-0 h-full w-full object-cover"
        muted
        playsInline
        controls
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={handlePlay}
        onPause={handlePause}
        onEnded={handleEnded}
      />

      <div className="pointer-events-none absolute inset-0">
        <CameraPreview
          videoRef={videoRef}
          poseLandmarks={poseLandmarks}
          showSkeleton
          mirror={false}
          hideVideo
          showChrome={false}
        />
      </div>
      <SessionHud elapsedSec={elapsedSec} repCount={frame.repCount} onClose={onClose} />

      <div className="absolute inset-x-4 top-18 z-20 flex justify-center">
        <label className="pointer-events-auto inline-flex max-w-[90vw] cursor-pointer items-center rounded-full border border-white/15 bg-black/45 px-4 py-2 text-sm font-semibold text-white/90 backdrop-blur-md">
          <input type="file" accept="video/*" className="hidden" onChange={handleFileChange} />
          <span className="truncate">
            {isVideoSelected ? `Đổi video: ${videoFileName}` : "Chọn video để debug"}
          </span>
        </label>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-col items-center gap-3 px-5 pb-6">
        <DebugStrip frame={frame} visible />
        <SessionGuide
          message={helperMessage}
          status={status}
          phase={frame.phase}
          calibrationProgress={frame.calibrationProgress}
          confidence={frame.confidence}
        />
      </div>
    </div>
  );
}
