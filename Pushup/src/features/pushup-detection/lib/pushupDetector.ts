import type { PoseLandmarkerResult } from "@mediapipe/tasks-vision";
import { CalibrationBuffer } from "./calibration";
import { getPoseMetrics } from "./landmarkMath";
import { EmaSmoother } from "./smoothing";
import { isRepDurationValid } from "./validator";
import { getThresholdsForPlatform } from "../model/constants";
import type { DetectorFrameState, DetectorPhase } from "../model/detectorTypes";

type Thresholds = ReturnType<typeof getThresholdsForPlatform>;
type PushupDetectorOptions = {
  flexibleCalibration?: boolean;
};

function createBaseFrameState(message: string): DetectorFrameState {
  return {
    status: "calibrating",
    phase: "unknown",
    repCount: 0,
    confidence: 0,
    fps: 0,
    calibrationProgress: 0,
    baseline: null,
    upThreshold: null,
    downThreshold: null,
    message,
    debug: {
      rawHeadHeight: null,
      smoothedHeadHeight: null,
      rawElbowAngle: null,
      smoothedElbowAngle: null,
      transitionFrom: "unknown",
      transitionTo: "unknown",
      transitionCompletedRep: false,
      reachedBottom: false,
      elapsedMsSinceLastRep: null,
      minRepDurationMs: null,
      maxRepDurationMs: null,
      calibrationMinAngle: null,
      calibrationAcceptedFrame: false,
      repBlockReason: "none",
    },
  };
}

function trackingMessage(phase: DetectorPhase, completedRep: boolean) {
  if (completedRep) {
    return "Tốt lắm, tiếp tục nhịp tiếp theo";
  }

  switch (phase) {
    case "up":
    case "going_down":
      return "Hạ người xuống chậm và sâu hơn";
    case "down":
    case "going_up":
      return "Đẩy người lên về đỉnh";
    default:
      return "Giữ nhịp ổn định để app bắt đúng chuyển động";
  }
}

function isBottomVerified(elbowAngle: number | null, elbowConfidence: number, threshold: number) {
  if (elbowAngle === null || elbowConfidence <= threshold) {
    return true;
  }

  return elbowAngle < 140;
}

function isTopVerified(elbowAngle: number | null, elbowConfidence: number, threshold: number) {
  if (elbowAngle === null || elbowConfidence <= threshold) {
    return true;
  }

  return elbowAngle > 145;
}

export class PushupDetector {
  private readonly thresholds: Thresholds;
  private readonly smoother: EmaSmoother;
  private readonly options: PushupDetectorOptions;
  private readonly calibration = new CalibrationBuffer();
  private baseline: number | null = null;
  private upThreshold: number | null = null;
  private downThreshold: number | null = null;
  private phase: DetectorPhase = "unknown";
  private repCount = 0;
  private lastRepTimestampMs = 0;
  private previousFrameTimestampMs = 0;
  private reachedBottom = false;

  constructor(userAgent: string, options: PushupDetectorOptions = {}) {
    this.thresholds = getThresholdsForPlatform(userAgent);
    this.options = options;
    this.smoother = new EmaSmoother(this.thresholds.emaAlpha);
  }

  process(result: PoseLandmarkerResult, timestampMs: number) {
    const frame = createBaseFrameState("Đưa cơ thể vào khung hình");
    const landmarks = result.landmarks[0];

    if (!landmarks) {
      frame.debug.repBlockReason = "missing_landmarks";
      return frame;
    }

    const metrics = getPoseMetrics(landmarks);
    const trackingConfidence = Math.min(metrics.shoulderConfidence, metrics.elbowConfidence);

    frame.confidence = trackingConfidence;
    frame.fps = this.previousFrameTimestampMs
      ? Math.round(1000 / Math.max(1, timestampMs - this.previousFrameTimestampMs))
      : 0;
    frame.debug.rawHeadHeight = metrics.headHeight;
    frame.debug.rawElbowAngle = metrics.elbowAngle;
    frame.debug.transitionFrom = this.phase;
    frame.debug.transitionTo = this.phase;
    frame.debug.reachedBottom = this.reachedBottom;
    frame.debug.minRepDurationMs = this.thresholds.minRepDurationMs;
    frame.debug.maxRepDurationMs = this.thresholds.maxRepDurationMs;
    this.previousFrameTimestampMs = timestampMs;

    if (metrics.headHeight === null) {
      frame.message = "Đưa đầu, vai hoặc hông vào khung hình";
      frame.debug.repBlockReason = "missing_landmarks";
      return frame;
    }

    const smoothedSignal = this.smoother.next(metrics.headHeight);
    frame.debug.smoothedHeadHeight = smoothedSignal;
    frame.debug.smoothedElbowAngle = metrics.elbowAngle;

    if (this.baseline === null) {
      const calibrationSignalThreshold = this.options.flexibleCalibration
        ? Math.max(0.015, this.thresholds.calibrationMinAngle * 0.6)
        : this.thresholds.calibrationMinAngle;
      const calibrationAcceptedFrame =
        trackingConfidence >= this.thresholds.confidenceThreshold &&
        smoothedSignal >= calibrationSignalThreshold;

      frame.calibrationProgress = this.calibration.progress;
      frame.message = "Giữ tư thế bắt đầu";
      frame.debug.repBlockReason = "calibrating";
      frame.debug.calibrationMinAngle = calibrationSignalThreshold;
      frame.debug.calibrationAcceptedFrame = calibrationAcceptedFrame;

      if (calibrationAcceptedFrame) {
        this.calibration.add(smoothedSignal);
      }

      const finalized = this.calibration.finalize(
        this.thresholds.upRatio,
        this.thresholds.downRatio,
      );

      if (!finalized) {
        frame.calibrationProgress = this.calibration.progress;
        return frame;
      }

      this.baseline = finalized.baseline;
      this.upThreshold = finalized.upThreshold;
      this.downThreshold = finalized.downThreshold;
      this.phase = "up";
      frame.calibrationProgress = 1;
      frame.baseline = this.baseline;
      frame.upThreshold = this.upThreshold;
      frame.downThreshold = this.downThreshold;
      frame.status = "tracking";
      frame.phase = this.phase;
      frame.debug.transitionTo = this.phase;
      frame.message = "Bắt đầu hít đất";
      return frame;
    }

    frame.status = "tracking";
    frame.baseline = this.baseline;
    frame.upThreshold = this.upThreshold;
    frame.downThreshold = this.downThreshold;
    frame.calibrationProgress = 1;

    if (
      trackingConfidence < this.thresholds.confidenceThreshold ||
      this.upThreshold === null ||
      this.downThreshold === null
    ) {
      frame.phase = this.phase;
      frame.repCount = this.repCount;
      frame.message = "Tín hiệu quá yếu, giữ vai và tay rõ hơn";
      frame.debug.repBlockReason = "low_confidence";
      return frame;
    }

    const bottomVerified = isBottomVerified(
      metrics.elbowAngle,
      metrics.elbowConfidence,
      this.thresholds.confidenceThreshold,
    );
    const topVerified = isTopVerified(
      metrics.elbowAngle,
      metrics.elbowConfidence,
      this.thresholds.confidenceThreshold,
    );

    let nextPhase = this.phase;
    let transitionCompletedRep = false;

    switch (this.phase) {
      case "unknown":
        nextPhase = smoothedSignal > this.upThreshold ? "up" : "unknown";
        break;
      case "up":
        if (smoothedSignal <= this.upThreshold) {
          nextPhase = "going_down";
        }
        break;
      case "going_down":
        if (smoothedSignal < this.downThreshold && bottomVerified) {
          nextPhase = "down";
        } else if (smoothedSignal > this.upThreshold) {
          nextPhase = "up";
        }
        break;
      case "down":
        if (smoothedSignal >= this.downThreshold) {
          nextPhase = "going_up";
        }
        break;
      case "going_up":
        if (smoothedSignal > this.upThreshold && topVerified) {
          nextPhase = "up";
          transitionCompletedRep = true;
        } else if (smoothedSignal < this.downThreshold) {
          nextPhase = "down";
        }
        break;
    }

    if (nextPhase === "down") {
      this.reachedBottom = true;
    }

    const elapsedMs = this.lastRepTimestampMs
      ? timestampMs - this.lastRepTimestampMs
      : Number.MAX_SAFE_INTEGER;
    frame.debug.elapsedMsSinceLastRep = this.lastRepTimestampMs ? elapsedMs : null;

    const completedRep =
      transitionCompletedRep &&
      this.reachedBottom &&
      isRepDurationValid({
        confidence: trackingConfidence,
        confidenceThreshold: this.thresholds.confidenceThreshold,
        elapsedMs,
        minRepDurationMs: this.thresholds.minRepDurationMs,
        maxRepDurationMs: this.thresholds.maxRepDurationMs,
      });

    let repBlockReason: DetectorFrameState["debug"]["repBlockReason"] = "none";
    if (this.phase === "going_down" && smoothedSignal <= this.downThreshold && !bottomVerified) {
      repBlockReason = "waiting_for_bottom";
    } else if (
      transitionCompletedRep &&
      elapsedMs < this.thresholds.minRepDurationMs
    ) {
      repBlockReason = "duration_too_short";
    } else if (
      transitionCompletedRep &&
      elapsedMs > this.thresholds.maxRepDurationMs
    ) {
      repBlockReason = "duration_too_long";
    } else if (
      this.phase === "going_up" &&
      smoothedSignal >= this.upThreshold &&
      !topVerified
    ) {
      repBlockReason = "waiting_for_full_extension";
    }

    this.phase = nextPhase;

    if (completedRep) {
      this.repCount += 1;
      this.lastRepTimestampMs = timestampMs;
      this.reachedBottom = false;
    }

    frame.phase = this.phase;
    frame.repCount = this.repCount;
    frame.message = trackingMessage(this.phase, completedRep);
    frame.debug.transitionTo = this.phase;
    frame.debug.transitionCompletedRep = transitionCompletedRep;
    frame.debug.reachedBottom = this.reachedBottom;
    frame.debug.repBlockReason = repBlockReason;

    return frame;
  }

  reset() {
    this.baseline = null;
    this.upThreshold = null;
    this.downThreshold = null;
    this.phase = "unknown";
    this.repCount = 0;
    this.lastRepTimestampMs = 0;
    this.previousFrameTimestampMs = 0;
    this.reachedBottom = false;
    this.smoother.reset();
    this.calibration.reset();
  }
}
