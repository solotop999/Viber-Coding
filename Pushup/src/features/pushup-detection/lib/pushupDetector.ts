import type { PoseLandmarkerResult } from "@mediapipe/tasks-vision";
import { getPoseMetrics } from "./landmarkMath";
import { EmaSmoother } from "./smoothing";
import { isRepDurationValid } from "./validator";
import { getThresholdsForPlatform } from "../model/constants";
import type { DetectorFrameState, DetectorPhase } from "../model/detectorTypes";

type Thresholds = ReturnType<typeof getThresholdsForPlatform>;

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
}

function trackingMessage(active: boolean, completedRep: boolean) {
  if (!active) {
    return "Dung vao tu the san sang";
  }

  if (completedRep) {
    return "Tot lam, tiep tuc nhip tiep theo";
  }

  return "Giu tu the on dinh va ro trong khung hinh";
}

function readinessMessage(checks: {
  faceVisible: boolean;
  shouldersVisible: boolean;
  hipsVisible: boolean;
  elbowsVisible: boolean;
  facingCamera: boolean;
}) {
  if (!checks.faceVisible) {
    return "Dua mat vao ro truoc camera";
  }

  if (!checks.shouldersVisible) {
    return "Can thay ro ca 2 vai";
  }

  if (!checks.hipsVisible) {
    return "Can thay ro ca 2 ben hong";
  }

  if (!checks.elbowsVisible) {
    return "Can thay ro ca 2 khuyu tay";
  }

  if (!checks.facingCamera) {
    return "Xoay mat doi dien camera";
  }

  return "Giu yen de xac nhan tu the san sang";
}

export class PushupDetector {
  private readonly thresholds: Thresholds;
  private readonly smoother: EmaSmoother;
  private phase: DetectorPhase = "unknown";
  private pendingPhase: DetectorPhase | null = null;
  private pendingPhaseFrames = 0;
  private repCount = 0;
  private lastRepTimestampMs = 0;
  private previousFrameTimestampMs = 0;
  private previousSmoothedSignal: number | null = null;
  private active = false;
  private readyToCount = false;
  private readyFrames = 0;

  constructor(userAgent: string) {
    this.thresholds = getThresholdsForPlatform(userAgent);
    this.smoother = new EmaSmoother(this.thresholds.emaAlpha);
  }

  private confirmPhase(nextPhase: DetectorPhase) {
    if (nextPhase === this.phase) {
      this.pendingPhase = null;
      this.pendingPhaseFrames = 0;
      return this.phase;
    }

    if (this.pendingPhase === nextPhase) {
      this.pendingPhaseFrames += 1;
    } else {
      this.pendingPhase = nextPhase;
      this.pendingPhaseFrames = 1;
    }

    if (this.pendingPhaseFrames >= this.thresholds.phaseConfirmFrames) {
      this.pendingPhase = null;
      this.pendingPhaseFrames = 0;
      return nextPhase;
    }

    return this.phase;
  }

  process(result: PoseLandmarkerResult, timestampMs: number) {
    const frame = createBaseFrameState("Dua mat va vai vao khung hinh");
    const landmarks = result.landmarks[0];

    frame.debug.active = this.active;
    frame.debug.readyToCount = this.readyToCount;
    frame.phase = this.phase;
    frame.repCount = this.repCount;
    frame.debug.transitionFrom = this.phase;
    frame.debug.transitionTo = this.phase;
    frame.debug.minRepDurationMs = this.thresholds.minRepDurationMs;
    frame.debug.maxRepDurationMs = this.thresholds.maxRepDurationMs;
    frame.debug.activationRange = this.thresholds.activationRange;
    frame.debug.readyProgress = Math.min(this.readyFrames / this.thresholds.readyHoldFrames, 1);

    if (!landmarks) {
      frame.debug.repBlockReason = "missing_landmarks";
      return frame;
    }

    const metrics = getPoseMetrics(landmarks);
    const trackingConfidence = metrics.shoulderConfidence;

    frame.confidence = trackingConfidence;
    frame.fps = this.previousFrameTimestampMs
      ? Math.round(1000 / Math.max(1, timestampMs - this.previousFrameTimestampMs))
      : 0;
    frame.debug.rawHeadHeight = metrics.headHeight;
    frame.debug.rawElbowAngle = metrics.elbowAngle;
    this.previousFrameTimestampMs = timestampMs;

    const faceVisible = metrics.noseConfidence >= this.thresholds.readyVisibilityThreshold;
    const shouldersVisible = metrics.shoulderConfidence >= this.thresholds.readyVisibilityThreshold;
    const hipsVisible = metrics.hipConfidence >= this.thresholds.readyVisibilityThreshold;
    const elbowsVisible = metrics.elbowJointConfidence >= this.thresholds.readyVisibilityThreshold;
    const facingCamera =
      metrics.noseOffsetFromShoulderCenterRatio !== null &&
      metrics.noseOffsetFromShoulderCenterRatio <= this.thresholds.readyFaceCenterToleranceRatio;
    const readyPose =
      faceVisible && shouldersVisible && hipsVisible && elbowsVisible && facingCamera;

    frame.debug.readyFaceVisible = faceVisible;
    frame.debug.readyShouldersVisible = shouldersVisible;
    frame.debug.readyHipsVisible = hipsVisible;
    frame.debug.readyElbowsVisible = elbowsVisible;
    frame.debug.readyFacingCamera = facingCamera;

    if (metrics.headHeight === null) {
      this.readyFrames = 0;
      frame.debug.repBlockReason = "missing_landmarks";
      frame.message = "Dua mat va vai ro hon vao khung hinh";
      return frame;
    }

    const rawSignal = metrics.headHeight;
    const smoothedSignal = this.smoother.next(rawSignal);
    const motionDelta =
      this.previousSmoothedSignal === null ? null : smoothedSignal - this.previousSmoothedSignal;
    const motionTrend =
      motionDelta === null
        ? "unknown"
        : motionDelta <= -this.thresholds.motionTrendThreshold
          ? "falling"
          : motionDelta >= this.thresholds.motionTrendThreshold
            ? "rising"
            : "steady";
    this.previousSmoothedSignal = smoothedSignal;
    frame.debug.smoothedHeadHeight = smoothedSignal;
    frame.debug.rawMotionSignal = rawSignal;
    frame.debug.smoothedMotionSignal = smoothedSignal;
    frame.debug.motionTrend = motionTrend;
    frame.debug.smoothedElbowAngle = metrics.elbowAngle;

    frame.baseline = 0;
    frame.upThreshold = this.thresholds.upPositionThreshold;
    frame.downThreshold = this.thresholds.downPositionThreshold;

    if (!this.readyToCount) {
      this.readyFrames = readyPose ? this.readyFrames + 1 : 0;
      frame.debug.readyProgress = Math.min(this.readyFrames / this.thresholds.readyHoldFrames, 1);
      frame.debug.repBlockReason = readyPose ? "none" : "waiting_for_ready";
      frame.message = readinessMessage({
        faceVisible,
        shouldersVisible,
        hipsVisible,
        elbowsVisible,
        facingCamera,
      });

      if (this.readyFrames >= this.thresholds.readyHoldFrames) {
        this.readyToCount = true;
        this.active = true;
        this.phase =
          smoothedSignal <= this.thresholds.downPositionThreshold
            ? "down"
            : smoothedSignal >= this.thresholds.upPositionThreshold
              ? "up"
              : "unknown";
        frame.debug.active = this.active;
        frame.debug.readyToCount = true;
        frame.phase = this.phase;
        frame.debug.transitionTo = this.phase;
        frame.message = "San sang, bat dau dem rep";
      } else {
        frame.phase = "unknown";
        frame.repCount = this.repCount;
        return frame;
      }
    }

    if (trackingConfidence < this.thresholds.confidenceThreshold) {
      frame.phase = this.phase;
      frame.repCount = this.repCount;
      frame.debug.repBlockReason = "low_confidence";
      frame.message = "Giu ro 2 vai trong khung hinh";
      frame.debug.readyToCount = this.readyToCount;
      return frame;
    }

    let candidatePhase = this.phase;
    let candidateCompletedRep = false;
    const upwardGate = this.thresholds.upPositionThreshold + this.thresholds.positionHysteresis;
    const downwardGate =
      this.thresholds.downPositionThreshold - this.thresholds.positionHysteresis;

    switch (this.phase) {
      case "unknown":
        if (smoothedSignal <= this.thresholds.downPositionThreshold) {
          candidatePhase = "down";
        } else if (smoothedSignal >= this.thresholds.upPositionThreshold) {
          candidatePhase = "up";
        }
        break;
      case "up":
        if (smoothedSignal <= this.thresholds.upPositionThreshold - this.thresholds.positionHysteresis) {
          candidatePhase = "going_down";
        }
        break;
      case "going_down":
        if (smoothedSignal <= downwardGate) {
          candidatePhase = "down";
        } else if (smoothedSignal >= upwardGate) {
          candidatePhase = "up";
        }
        break;
      case "down":
        if (smoothedSignal >= this.thresholds.downPositionThreshold + this.thresholds.positionHysteresis) {
          candidatePhase = "going_up";
        }
        break;
      case "going_up":
        if (smoothedSignal >= upwardGate) {
          candidatePhase = "up";
          candidateCompletedRep = true;
        } else if (smoothedSignal <= downwardGate) {
          candidatePhase = "down";
        }
        break;
    }

    const previousPhase = this.phase;
    const nextPhase = this.confirmPhase(candidatePhase);
    const transitionCompletedRep =
      candidateCompletedRep && nextPhase === candidatePhase && nextPhase !== previousPhase;

    const hasPreviousRep = this.lastRepTimestampMs > 0;
    const elapsedMs = hasPreviousRep
      ? timestampMs - this.lastRepTimestampMs
      : this.thresholds.minRepDurationMs;
    frame.debug.elapsedMsSinceLastRep = hasPreviousRep ? elapsedMs : null;

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
    if (transitionCompletedRep && hasPreviousRep && elapsedMs < this.thresholds.minRepDurationMs) {
      repBlockReason = "duration_too_short";
    } else if (
      transitionCompletedRep &&
      hasPreviousRep &&
      elapsedMs > this.thresholds.maxRepDurationMs
    ) {
      repBlockReason = "duration_too_long";
    }

    this.phase = nextPhase;

    if (completedRep) {
      this.repCount += 1;
      this.lastRepTimestampMs = timestampMs;
    } else if (this.phase === "up" && hasPreviousRep && elapsedMs > this.thresholds.maxRepDurationMs) {
      this.lastRepTimestampMs = 0;
    }

    frame.debug.active = this.active;
    frame.debug.readyToCount = this.readyToCount;
    frame.phase = this.phase;
    frame.repCount = this.repCount;
    frame.message = trackingMessage(this.active, completedRep);
    frame.debug.transitionTo = this.phase;
    frame.debug.transitionCompletedRep = transitionCompletedRep;
    frame.debug.reachedBottom = this.phase === "down" || this.phase === "going_up";
    frame.debug.repBlockReason = repBlockReason;

    return frame;
  }

  reset() {
    this.phase = "unknown";
    this.pendingPhase = null;
    this.pendingPhaseFrames = 0;
    this.repCount = 0;
    this.lastRepTimestampMs = 0;
    this.previousFrameTimestampMs = 0;
    this.previousSmoothedSignal = null;
    this.active = false;
    this.readyToCount = false;
    this.readyFrames = 0;
    this.smoother.reset();
  }

  resetForReplay() {
    this.phase = "unknown";
    this.pendingPhase = null;
    this.pendingPhaseFrames = 0;
    this.lastRepTimestampMs = 0;
    this.previousFrameTimestampMs = 0;
    this.previousSmoothedSignal = null;
    this.active = false;
    this.readyToCount = false;
    this.readyFrames = 0;
    this.smoother.reset();
  }
}
