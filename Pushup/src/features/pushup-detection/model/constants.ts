export const PUSHUP_STORAGE_KEY = "pushup-sessions";

export const TODAY_GOAL = 100;
export const HISTORY_LIMIT = 7;
export const DETECTION_INTERVAL_MS = 1000 / 15;
export const COUNTDOWN_SECONDS = 3;
export const CALIBRATION_FRAME_TARGET = 25;

export const MEDIAPIPE_WASM_BASE_URL =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.34/wasm";
export const POSE_MODEL_ASSET_URL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task";

export const DEFAULT_THRESHOLDS = {
  upRatio: 0.75,
  downRatio: 0.52,
  emaAlpha: 0.5,
  confidenceThreshold: 0.45,
  minRepDurationMs: 500,
  maxRepDurationMs: 12000,
  calibrationMinAngle: 0.03,
};

export function getThresholdsForPlatform(userAgent: string) {
  const isIosSafari =
    /iPhone|iPad|iPod/i.test(userAgent) &&
    /Safari/i.test(userAgent) &&
    !/CriOS|FxiOS|EdgiOS/i.test(userAgent);

  if (!isIosSafari) {
    return DEFAULT_THRESHOLDS;
  }

  return {
    ...DEFAULT_THRESHOLDS,
    confidenceThreshold: 0.4,
  };
}
