import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import type { NormalizedLandmark } from "@mediapipe/tasks-vision";
import CameraPreview from "./CameraPreview";
import DebugStrip from "./DebugStrip";
import ReadyCheckOverlay from "./ReadyCheckOverlay";
import SessionGuide from "./SessionGuide";
import SessionHud from "./SessionHud";
import { loadPoseLandmarker } from "../lib/mediapipeLoader";
import { PushupDetector } from "../lib/pushupDetector";
import { DETECTION_INTERVAL_MS } from "../model/constants";
import type { DetectorFrameState, DetectorPhase, DetectorStatus } from "../model/detectorTypes";

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
  message: "Chon video de debug",
  debug: {
    active: false,
    rawHeadHeight: null,
    smoothedHeadHeight: null,
    rawMotionSignal: null,
    smoothedMotionSignal: null,
    motionTrend: "unknown",
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
    readyToCount: false,
    readyProgress: 0,
    readyFaceVisible: false,
    readyShouldersVisible: false,
    readyHipsVisible: false,
    readyElbowsVisible: false,
    readyFacingCamera: false,
    repBlockReason: "none",
  },
};

const DEFAULT_DEBUG_VIDEO_URL = "/vidu.mp4";
const DEFAULT_DEBUG_VIDEO_NAME = "vidu.mp4";
const PLAYBACK_RATES = [0.25, 0.5, 0.75, 1] as const;
const SHOW_DEBUG_UI = true;

type DebugLogEntry = {
  event: "frame" | "loop_restart" | "session_reset";
  wallClockIso: string;
  nowMs: number;
  videoTimestampMs: number;
  elapsedSec: number;
  playbackRate: number;
  status: DetectorStatus;
  phase: DetectorPhase;
  message: string;
  totalRepCount: number;
  loopRepCount: number;
  repOffset: number;
  confidence: number;
  fps: number;
  active: boolean;
  rawMotionSignal: number | null;
  smoothedMotionSignal: number | null;
  rawElbowAngle: number | null;
  smoothedElbowAngle: number | null;
  upThreshold: number | null;
  downThreshold: number | null;
  transitionFrom: DetectorPhase;
  transitionTo: DetectorPhase;
  transitionCompletedRep: boolean;
  reachedBottom: boolean;
  repBlockReason: DetectorFrameState["debug"]["repBlockReason"];
  oscillationRange: number;
  bufferFill: number;
  elapsedMsSinceLastRep: number | null;
};

export default function VideoDebugScreen({ onClose }: VideoDebugScreenProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const requestRef = useRef<number | null>(null);
  const detectorRef = useRef<PushupDetector | null>(null);
  const poseLandmarkerRef = useRef<Awaited<ReturnType<typeof loadPoseLandmarker>> | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const lastDetectionAtRef = useRef(0);
  const lastVideoTimestampRef = useRef(-1);
  const debugLogRef = useRef<DebugLogEntry[]>([]);
  const isLoggingRef = useRef(false);
  const playbackRateRef = useRef<(typeof PLAYBACK_RATES)[number]>(0.5);
  const frameRef = useRef<DetectorFrameState>(initialFrame);

  const [poseLandmarks, setPoseLandmarks] = useState<NormalizedLandmark[]>([]);
  const [frame, setFrame] = useState<DetectorFrameState>(initialFrame);
  const [status, setStatus] = useState<DetectorStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [videoFileName, setVideoFileName] = useState("");
  const [elapsedSec, setElapsedSec] = useState(0);
  const [playbackRate, setPlaybackRate] = useState<(typeof PLAYBACK_RATES)[number]>(0.5);
  const [isLogging, setIsLogging] = useState(false);

  const isVideoSelected = Boolean(videoFileName);

  useEffect(() => {
    playbackRateRef.current = playbackRate;
  }, [playbackRate]);

  useEffect(() => {
    frameRef.current = frame;
  }, [frame]);

  useEffect(() => {
    isLoggingRef.current = isLogging;
  }, [isLogging]);

  function resetDebugState(message: string) {
    detectorRef.current?.reset();
    lastDetectionAtRef.current = 0;
    lastVideoTimestampRef.current = -1;
    debugLogRef.current = [];
    setPoseLandmarks([]);
    setElapsedSec(0);
    setStatus("idle");
    setError(null);
    setIsLogging(false);
    setFrame({ ...initialFrame, message });
  }

  function appendDebugLog(entry: DebugLogEntry) {
    if (!isLoggingRef.current) {
      return;
    }

    debugLogRef.current.push(entry);
  }

  function buildLogEntry(params: {
    event: DebugLogEntry["event"];
    frame: DetectorFrameState;
    nowMs: number;
    videoTimestampMs: number;
    elapsedSec: number;
    playbackRate: number;
  }): DebugLogEntry {
    const { event, frame, nowMs, videoTimestampMs, elapsedSec, playbackRate } = params;

    return {
      event,
      wallClockIso: new Date().toISOString(),
      nowMs,
      videoTimestampMs,
      elapsedSec,
      playbackRate,
      status: frame.status,
      phase: frame.phase,
      message: frame.message,
      totalRepCount: frame.repCount,
      loopRepCount: frame.repCount,
      repOffset: 0,
      confidence: frame.confidence,
      fps: frame.fps,
      active: frame.debug.active,
      rawMotionSignal: frame.debug.rawMotionSignal,
      smoothedMotionSignal: frame.debug.smoothedMotionSignal,
      rawElbowAngle: frame.debug.rawElbowAngle,
      smoothedElbowAngle: frame.debug.smoothedElbowAngle,
      upThreshold: frame.upThreshold,
      downThreshold: frame.downThreshold,
      transitionFrom: frame.debug.transitionFrom,
      transitionTo: frame.debug.transitionTo,
      transitionCompletedRep: frame.debug.transitionCompletedRep,
      reachedBottom: frame.debug.reachedBottom,
      repBlockReason: frame.debug.repBlockReason,
      oscillationRange: frame.debug.oscillationRange,
      bufferFill: frame.debug.bufferFill,
      elapsedMsSinceLastRep: frame.debug.elapsedMsSinceLastRep,
    };
  }

  function restartTrackingLoop(video: HTMLVideoElement) {
    appendDebugLog(
      buildLogEntry({
        event: "loop_restart",
        frame: frameRef.current,
        nowMs: performance.now(),
        videoTimestampMs: video.currentTime * 1000,
        elapsedSec: Math.floor(video.currentTime),
        playbackRate: playbackRateRef.current,
      }),
    );

    detectorRef.current?.resetForReplay();
    lastDetectionAtRef.current = 0;
    lastVideoTimestampRef.current = -1;
    setPoseLandmarks([]);
    setElapsedSec(0);
    setFrame((current) => ({ ...current }));
    video.currentTime = 0;
  }

  function attemptAutoplay(video: HTMLVideoElement) {
    void video.play().catch(() => {
      setStatus((current) => (current === "error" ? current : "paused"));
      setFrame((current) => ({
        ...current,
        status: "paused",
        message: "Video da san sang, neu autoplay bi chan thi bam Play",
      }));
    });
  }

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
        setError("Khong tai duoc bo nhan dien cho che do debug video.");
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
    resetDebugState("Da nap video mau, dang chuan bi tracking");
  }, [isVideoSelected]);

  useEffect(() => {
    const video = videoRef.current;

    if (!video) {
      return;
    }

    video.playbackRate = playbackRate;
    video.defaultPlaybackRate = playbackRate;
  }, [playbackRate]);

  useEffect(() => {
    const tick = () => {
      const now = performance.now();
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
      if (timestampMs < lastVideoTimestampRef.current) {
        restartTrackingLoop(video);
        requestRef.current = requestAnimationFrame(tick);
        return;
      }

      if (now - lastDetectionAtRef.current < DETECTION_INTERVAL_MS) {
        requestRef.current = requestAnimationFrame(tick);
        return;
      }

      lastDetectionAtRef.current = now;
      lastVideoTimestampRef.current = timestampMs;
      const result = poseLandmarker.detectForVideo(video, now);
      const nextFrame = detector.process(result, timestampMs);
      appendDebugLog(
        buildLogEntry({
          event: "frame",
          frame: nextFrame,
          nowMs: now,
          videoTimestampMs: timestampMs,
          elapsedSec: Math.floor(video.currentTime),
          playbackRate: playbackRateRef.current,
        }),
      );

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
    resetDebugState("Da nap video, dang chuan bi tracking");
  }

  function handleExportLog() {
    if (!debugLogRef.current.length) {
      return;
    }

    const payload = {
      exportedAt: new Date().toISOString(),
      videoFileName: videoFileName || DEFAULT_DEBUG_VIDEO_NAME,
      playbackRate,
      entryCount: debugLogRef.current.length,
      entries: debugLogRef.current,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    link.href = url;
    link.download = `pushup-debug-${timestamp}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function handleResetLog() {
    debugLogRef.current = [];
    setFrame((current) => ({ ...current }));
  }

  function handleToggleLog() {
    setIsLogging((current) => !current);
  }

  function handleLoadedMetadata() {
    const video = videoRef.current;
    resetDebugState("Video san sang, dang chay detection");
    if (video) {
      video.playbackRate = playbackRate;
      video.defaultPlaybackRate = playbackRate;
      attemptAutoplay(video);
    }
  }

  function handlePlay() {
    setStatus((current) => (current === "idle" ? "tracking" : current));
    setError(null);
  }

  function handlePause() {
    if (videoRef.current?.ended) {
      const video = videoRef.current;
      if (video) {
        restartTrackingLoop(video);
        attemptAutoplay(video);
      }
      return;
    }

    setStatus("paused");
    setFrame((current) => ({ ...current, status: "paused" }));
  }

  function handleEnded() {
    const video = videoRef.current;

    if (!video) {
      return;
    }

    restartTrackingLoop(video);
    attemptAutoplay(video);
  }

  const helperMessage = useMemo(() => {
    if (error) {
      return error;
    }

    if (!isVideoSelected) {
      return "Chon video hit dat de xem pose va detector chay tren tung frame.";
    }

    return frame.message;
  }, [error, frame.message, isVideoSelected]);

  const logEntryCount = debugLogRef.current.length;
  const displayFrame = useMemo(() => frame, [frame]);

  return (
    <div className="relative h-full min-h-screen overflow-hidden bg-black text-white">
      <video
        ref={videoRef}
        className="absolute inset-0 h-full w-full object-cover"
        muted
        playsInline
        autoPlay
        loop
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
      <ReadyCheckOverlay ready={displayFrame.debug.readyToCount} />
      <SessionHud elapsedSec={elapsedSec} repCount={displayFrame.repCount} onClose={onClose} />

      {SHOW_DEBUG_UI ? (
        <div className="absolute left-3 top-16 z-20">
          <DebugStrip frame={displayFrame} visible />
        </div>
      ) : null}

      <div className="absolute inset-x-4 top-18 z-20 flex justify-center">
        <label className="pointer-events-auto inline-flex max-w-[90vw] cursor-pointer items-center rounded-full border border-white/15 bg-black/45 px-4 py-2 text-sm font-semibold text-white/90 backdrop-blur-md">
          <input type="file" accept="video/*" className="hidden" onChange={handleFileChange} />
          <span className="truncate">
            {isVideoSelected ? `Doi video: ${videoFileName}` : "Chon video de debug"}
          </span>
        </label>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-col items-start gap-3 px-5 pb-6">
        {SHOW_DEBUG_UI ? (
          <div className="pointer-events-auto inline-flex max-w-[92vw] flex-wrap items-center justify-start gap-x-4 gap-y-2 rounded-lg border border-white/20 bg-black px-3 py-2 text-white backdrop-blur-md">
            <div className="inline-flex flex-wrap items-center justify-start gap-1.5">
              <span className="mr-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-white/70">
                Toc do
              </span>
              {PLAYBACK_RATES.map((rate) => {
                const active = playbackRate === rate;

                return (
                  <button
                    key={rate}
                    type="button"
                    onClick={() => setPlaybackRate(rate)}
                    className={`rounded-md px-2.5 py-1 text-[12px] font-semibold transition ${
                      active
                        ? "border border-white bg-white text-black"
                        : "border border-white/20 bg-black text-white"
                    }`}
                  >
                    {rate}x
                  </button>
                );
              })}
            </div>

            <div className="inline-flex flex-wrap items-center justify-start gap-1.5">
              <span className="mr-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-white/70">
                Log
              </span>
              <button
                type="button"
                onClick={handleToggleLog}
                className={`rounded-md px-2.5 py-1 text-[12px] font-semibold transition ${
                  isLogging
                    ? "border border-white bg-white text-black"
                    : "border border-white/20 bg-black text-white"
                }`}
              >
                {isLogging ? "Tat log" : "Bat log"}
              </button>
              <span className="rounded-md border border-white/20 bg-black px-2.5 py-1 text-[12px] font-semibold text-white">
                {logEntryCount} dong
              </span>
              <button
                type="button"
                onClick={handleExportLog}
                disabled={logEntryCount === 0}
                className="rounded-md border border-white/20 bg-black px-2.5 py-1 text-[12px] font-semibold text-white disabled:opacity-40"
              >
                Tai log
              </button>
              <button
                type="button"
                onClick={handleResetLog}
                className="rounded-md border border-white/20 bg-black px-2.5 py-1 text-[12px] font-semibold text-white"
              >
                Xoa log
              </button>
            </div>
          </div>
        ) : null}

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
