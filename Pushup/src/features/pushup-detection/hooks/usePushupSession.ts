import { useEffect, useMemo, useRef, useState } from "react";
import type { NormalizedLandmark } from "@mediapipe/tasks-vision";
import { DETECTION_INTERVAL_MS, COUNTDOWN_SECONDS } from "../model/constants";
import type { DetectorFrameState, DetectorStatus } from "../model/detectorTypes";
import { loadPoseLandmarker } from "../lib/mediapipeLoader";
import { PushupDetector } from "../lib/pushupDetector";
import { saveCompletedSession } from "../lib/sessionStorage";
import type { PushupSessionRecord } from "../model/sessionTypes";
import { useCamera } from "./useCamera";
import { useVisibilityPause } from "./useVisibilityPause";
import { useWakeLock } from "./useWakeLock";

type SessionState = {
  status: DetectorStatus;
  frame: DetectorFrameState;
  elapsedSec: number;
  error: string | null;
  poseLandmarks: NormalizedLandmark[];
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
  message: "Chuan bi",
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

export function usePushupSession() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const requestRef = useRef<number | null>(null);
  const lastDetectionRef = useRef(0);
  const detectorRef = useRef<PushupDetector | null>(null);
  const poseLandmarkerRef = useRef<Awaited<ReturnType<typeof loadPoseLandmarker>> | null>(null);
  const startedAtRef = useRef<number>(Date.now());
  const countdownStartedAtRef = useRef<number | null>(null);
  const fpsSamplesRef = useRef<number[]>([]);

  const [state, setState] = useState<SessionState>({
    status: "requesting_camera",
    frame: initialFrame,
    elapsedSec: 0,
    error: null,
    poseLandmarks: [],
  });

  const isHidden = useVisibilityPause();
  const camera = useCamera(videoRef, true);
  useWakeLock(!isHidden);

  const frame = state.frame;

  useEffect(() => {
    if (camera.error) {
      setState((current) => ({
        ...current,
        status: "error",
        error: camera.error,
        frame: { ...current.frame, status: "error", message: camera.error ?? "Loi camera" },
        poseLandmarks: [],
      }));
    }
  }, [camera.error]);

  useEffect(() => {
    if (!camera.isReady || camera.error) {
      return;
    }

    let cancelled = false;

    async function prepare() {
      try {
        const poseLandmarker = await loadPoseLandmarker();
        if (cancelled) {
          return;
        }

        detectorRef.current = new PushupDetector(navigator.userAgent);
        poseLandmarkerRef.current = poseLandmarker;
        countdownStartedAtRef.current = performance.now();
        startedAtRef.current = Date.now();
        fpsSamplesRef.current = [];
        setState((current) => ({
          ...current,
          status: "countdown",
          error: null,
          frame: { ...current.frame, status: "countdown", message: "Sap bat dau" },
          poseLandmarks: [],
        }));
      } catch {
        setState((current) => ({
          ...current,
          status: "error",
          error: "Khong tai duoc bo nhan dien tu the.",
          frame: {
            ...current.frame,
            status: "error",
            message: "Khong tai duoc bo nhan dien tu the.",
          },
          poseLandmarks: [],
        }));
      }
    }

    void prepare();

    return () => {
      cancelled = true;
    };
  }, [camera.error, camera.isReady]);

  useEffect(() => {
    if (!camera.isReady || state.status === "error") {
      return;
    }

    const tick = () => {
      const now = performance.now();
      const video = videoRef.current;
      const detector = detectorRef.current;
      const poseLandmarker = poseLandmarkerRef.current;

      if (!video || !detector || !poseLandmarker) {
        requestRef.current = requestAnimationFrame(tick);
        return;
      }

      if (isHidden) {
        setState((current) => ({
          ...current,
          status: "paused",
          frame: { ...current.frame, status: "paused", message: "Da tam dung khi chay nen" },
          poseLandmarks: current.poseLandmarks,
        }));
        requestRef.current = requestAnimationFrame(tick);
        return;
      }

      const countdownStartedAt = countdownStartedAtRef.current;
      if (countdownStartedAt !== null) {
        const remainingSeconds = Math.max(
          0,
          COUNTDOWN_SECONDS - Math.floor((now - countdownStartedAt) / 1000),
        );
        if (now - countdownStartedAt < COUNTDOWN_SECONDS * 1000) {
          setState((current) => ({
            ...current,
            status: "countdown",
            elapsedSec: Math.floor((Date.now() - startedAtRef.current) / 1000),
            frame: {
              ...current.frame,
              status: "countdown",
              message: remainingSeconds > 0 ? `Bat dau sau ${remainingSeconds}` : "Bat dau",
            },
          }));
          requestRef.current = requestAnimationFrame(tick);
          return;
        }
        countdownStartedAtRef.current = null;
      }

      if (now - lastDetectionRef.current < DETECTION_INTERVAL_MS || video.readyState < 2) {
        requestRef.current = requestAnimationFrame(tick);
        return;
      }

      lastDetectionRef.current = now;
      const result = poseLandmarker.detectForVideo(video, now);
      const nextFrame = detector.process(result, now);
      fpsSamplesRef.current.push(nextFrame.fps);
      const poseLandmarks = result.landmarks[0] ?? [];

      setState((current) => ({
        ...current,
        status: nextFrame.status,
        elapsedSec: Math.floor((Date.now() - startedAtRef.current) / 1000),
        frame: nextFrame,
        poseLandmarks,
      }));

      requestRef.current = requestAnimationFrame(tick);
    };

    requestRef.current = requestAnimationFrame(tick);

    return () => {
      if (requestRef.current !== null) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [camera.isReady, isHidden, state.status]);

  useEffect(() => {
    return () => {
      if (requestRef.current !== null) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, []);

  const sessionRecord = useMemo<PushupSessionRecord | null>(() => {
    if (frame.repCount <= 0) {
      return null;
    }

    const endedAt = new Date();
    const averageFps = fpsSamplesRef.current.length
      ? Math.round(
          fpsSamplesRef.current.reduce((sum, value) => sum + value, 0) / fpsSamplesRef.current.length,
        )
      : undefined;

    return {
      id: crypto.randomUUID(),
      startedAt: new Date(startedAtRef.current).toISOString(),
      endedAt: endedAt.toISOString(),
      durationSec: Math.max(1, Math.round((endedAt.getTime() - startedAtRef.current) / 1000)),
      repCount: frame.repCount,
      deviceMode: "front-camera",
      averageFps,
    };
  }, [frame.repCount]);

  function finishSession() {
    if (sessionRecord) {
      saveCompletedSession(sessionRecord);
    }
  }

  return {
    videoRef,
    frame,
    status: state.status,
    elapsedSec: state.elapsedSec,
    error: state.error,
    isCameraReady: camera.isReady,
    poseLandmarks: state.poseLandmarks,
    finishSession,
  };
}
