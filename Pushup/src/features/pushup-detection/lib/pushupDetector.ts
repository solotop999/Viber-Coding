import type { PoseLandmarkerResult } from "@mediapipe/tasks-vision";
import { getPoseMetrics } from "./landmarkMath";
import { EmaSmoother } from "./smoothing";
import { isRepDurationValid } from "./validator";
import { getThresholdsForPlatform } from "../model/constants";
import type { DetectorFrameState, DetectorPhase } from "../model/detectorTypes";

type Thresholds = ReturnType<typeof getThresholdsForPlatform>;

type BufferEntry = {
  timestampMs: number;
  value: number;
};

function createBaseFrameState(message: string): DetectorFrameState {
  return {
    status: "tracking",
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
}

function trackingMessage(active: boolean, phase: DetectorPhase, completedRep: boolean) {
  if (!active) {
    return "Sẵn sàng — bắt đầu hít đi";
  }

  if (completedRep) {
    return "Tốt lắm, tiếp tục nhịp tiếp theo";
  }

  switch (phase) {
    case "up":
    case "going_down":
      return "Hạ xuống";
    case "down":
    case "going_up":
      return "Đẩy lên";
    default:
      return "Đang theo dõi";
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
  private readonly rangeBuffer: BufferEntry[] = [];
  private phase: DetectorPhase = "unknown";
  private repCount = 0;
  private lastRepTimestampMs = 0;
  private previousFrameTimestampMs = 0;
  private active = false;

  constructor(userAgent: string) {
    this.thresholds = getThresholdsForPlatform(userAgent);
    this.smoother = new EmaSmoother(this.thresholds.emaAlpha);
  }

  process(result: PoseLandmarkerResult, timestampMs: number) {
    const frame = createBaseFrameState("Đưa mặt và vai vào khung hình");
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
    frame.debug.active = this.active;
    frame.debug.rawHeadHeight = metrics.headHeight;
    frame.debug.rawElbowAngle = metrics.elbowAngle;
    frame.debug.transitionFrom = this.phase;
    frame.debug.transitionTo = this.phase;
    frame.debug.minRepDurationMs = this.thresholds.minRepDurationMs;
    frame.debug.maxRepDurationMs = this.thresholds.maxRepDurationMs;
    frame.debug.activationRange = this.thresholds.activationRange;
    this.previousFrameTimestampMs = timestampMs;

    if (metrics.headHeight === null) {
      frame.debug.repBlockReason = "missing_landmarks";
      frame.message = "Đưa mặt và vai rõ hơn vào khung hình";
      return frame;
    }

    const rawSignal = metrics.headHeight;
    const smoothedSignal = this.smoother.next(rawSignal);
    frame.debug.smoothedHeadHeight = smoothedSignal;
    frame.debug.rawMotionSignal = rawSignal;
    frame.debug.smoothedMotionSignal = smoothedSignal;
    frame.debug.smoothedElbowAngle = metrics.elbowAngle;

    this.rangeBuffer.push({ timestampMs, value: smoothedSignal });
    while (
      this.rangeBuffer.length &&
      timestampMs - this.rangeBuffer[0].timestampMs > this.thresholds.baselineWindowMs
    ) {
      this.rangeBuffer.shift();
    }

    const minSignal = this.rangeBuffer.reduce(
      (min, entry) => Math.min(min, entry.value),
      Number.POSITIVE_INFINITY,
    );
    const maxSignal = this.rangeBuffer.reduce(
      (max, entry) => Math.max(max, entry.value),
      Number.NEGATIVE_INFINITY,
    );
    const oscillationRange =
      Number.isFinite(minSignal) && Number.isFinite(maxSignal) ? maxSignal - minSignal : 0;
    const bufferDurationMs =
      this.rangeBuffer.length >= 2
        ? this.rangeBuffer[this.rangeBuffer.length - 1].timestampMs -
          this.rangeBuffer[0].timestampMs
        : 0;
    const bufferFill = Math.min(bufferDurationMs / this.thresholds.baselineWindowMs, 1);

    frame.baseline = 0;
    frame.upThreshold = this.thresholds.upPositionThreshold;
    frame.downThreshold = this.thresholds.downPositionThreshold;
    frame.debug.oscillationRange = oscillationRange;
    frame.debug.bufferFill = bufferFill;

    if (trackingConfidence < this.thresholds.confidenceThreshold) {
      frame.phase = this.phase;
      frame.repCount = this.repCount;
      frame.debug.repBlockReason = "low_confidence";
      frame.message = "Giữ mặt, vai và tay rõ hơn";
      return frame;
    }

    const activationReady =
      this.rangeBuffer.length > 0 &&
      timestampMs - this.rangeBuffer[0].timestampMs >= this.thresholds.minBufferForActivationMs;

    if (!this.active) {
      if (activationReady && oscillationRange >= this.thresholds.activationRange) {
        this.active = true;
        this.phase =
          smoothedSignal <= this.thresholds.downPositionThreshold
            ? "down"
            : smoothedSignal >= this.thresholds.upPositionThreshold
              ? "up"
              : "unknown";
      }

      frame.debug.active = this.active;
      frame.phase = this.phase;
      frame.repCount = this.repCount;
      frame.debug.transitionTo = this.phase;
      frame.debug.repBlockReason = this.active ? "none" : "waiting_for_activation";
      frame.message = trackingMessage(this.active, this.phase, false);
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
        if (smoothedSignal <= this.thresholds.downPositionThreshold) {
          nextPhase = "down";
        } else if (smoothedSignal >= this.thresholds.upPositionThreshold) {
          nextPhase = "up";
        }
        break;
      case "up":
        if (smoothedSignal <= this.thresholds.upPositionThreshold) {
          nextPhase = "going_down";
        }
        break;
      case "going_down":
        if (smoothedSignal < this.thresholds.downPositionThreshold && bottomVerified) {
          nextPhase = "down";
        } else if (smoothedSignal > this.thresholds.upPositionThreshold) {
          nextPhase = "up";
        }
        break;
      case "down":
        if (smoothedSignal >= this.thresholds.downPositionThreshold) {
          nextPhase = "going_up";
        }
        break;
      case "going_up":
        if (smoothedSignal > this.thresholds.upPositionThreshold && topVerified) {
          nextPhase = "up";
          transitionCompletedRep = true;
        } else if (smoothedSignal < this.thresholds.downPositionThreshold) {
          nextPhase = "down";
        }
        break;
    }

    const elapsedMs = this.lastRepTimestampMs
      ? timestampMs - this.lastRepTimestampMs
      : Number.MAX_SAFE_INTEGER;
    frame.debug.elapsedMsSinceLastRep = this.lastRepTimestampMs ? elapsedMs : null;

    const completedRep =
      transitionCompletedRep &&
      isRepDurationValid({
        confidence: trackingConfidence,
        confidenceThreshold: this.thresholds.confidenceThreshold,
        elapsedMs,
        minRepDurationMs: this.thresholds.minRepDurationMs,
        maxRepDurationMs: this.thresholds.maxRepDurationMs,
      });

    let repBlockReason: DetectorFrameState["debug"]["repBlockReason"] = "none";
    if (
      this.phase === "going_down" &&
      smoothedSignal <= this.thresholds.downPositionThreshold &&
      !bottomVerified
    ) {
      repBlockReason = "waiting_for_bottom";
    } else if (transitionCompletedRep && elapsedMs < this.thresholds.minRepDurationMs) {
      repBlockReason = "duration_too_short";
    } else if (transitionCompletedRep && elapsedMs > this.thresholds.maxRepDurationMs) {
      repBlockReason = "duration_too_long";
    } else if (
      this.phase === "going_up" &&
      smoothedSignal >= this.thresholds.upPositionThreshold &&
      !topVerified
    ) {
      repBlockReason = "waiting_for_full_extension";
    }

    this.phase = nextPhase;

    if (completedRep) {
      this.repCount += 1;
      this.lastRepTimestampMs = timestampMs;
    } else if (this.phase === "up" && elapsedMs > this.thresholds.maxRepDurationMs) {
      this.lastRepTimestampMs = 0;
    }

    frame.debug.active = this.active;
    frame.phase = this.phase;
    frame.repCount = this.repCount;
    frame.message = trackingMessage(this.active, this.phase, completedRep);
    frame.debug.transitionTo = this.phase;
    frame.debug.transitionCompletedRep = transitionCompletedRep;
    frame.debug.reachedBottom = this.phase === "down" || this.phase === "going_up";
    frame.debug.repBlockReason = repBlockReason;

    return frame;
  }

  reset() {
    this.phase = "unknown";
    this.repCount = 0;
    this.lastRepTimestampMs = 0;
    this.previousFrameTimestampMs = 0;
    this.active = false;
    this.rangeBuffer.length = 0;
    this.smoother.reset();
  }
}
