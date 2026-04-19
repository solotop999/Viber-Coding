import type { PoseLandmarkerResult } from "@mediapipe/tasks-vision";

export type DetectorStatus =
  | "idle"
  | "requesting_camera"
  | "countdown"
  | "calibrating"
  | "tracking"
  | "paused"
  | "error"
  | "finished";

export type DetectorPhase = "up" | "going_down" | "down" | "going_up" | "unknown";

export type DetectorRepBlockReason =
  | "none"
  | "missing_landmarks"
  | "low_confidence"
  | "calibrating"
  | "duration_too_short"
  | "duration_too_long"
  | "waiting_for_bottom"
  | "waiting_for_full_extension";

export type DetectorDebugState = {
  rawHeadHeight: number | null;
  smoothedHeadHeight: number | null;
  rawElbowAngle: number | null;
  smoothedElbowAngle: number | null;
  transitionFrom: DetectorPhase;
  transitionTo: DetectorPhase;
  transitionCompletedRep: boolean;
  reachedBottom: boolean;
  elapsedMsSinceLastRep: number | null;
  minRepDurationMs: number | null;
  maxRepDurationMs: number | null;
  calibrationMinAngle: number | null;
  calibrationAcceptedFrame: boolean;
  repBlockReason: DetectorRepBlockReason;
};

export type DetectorFrameState = {
  status: DetectorStatus;
  phase: DetectorPhase;
  repCount: number;
  confidence: number;
  fps: number;
  calibrationProgress: number;
  baseline: number | null;
  upThreshold: number | null;
  downThreshold: number | null;
  message: string;
  debug: DetectorDebugState;
};

export type DetectorSnapshot = {
  result: PoseLandmarkerResult;
  timestampMs: number;
};

export type PoseMetrics = {
  headHeight: number | null;
  elbowAngle: number | null;
  shoulderConfidence: number;
  elbowConfidence: number;
  confidence: number;
};
