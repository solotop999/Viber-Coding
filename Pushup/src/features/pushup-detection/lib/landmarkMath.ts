import type { NormalizedLandmark } from "@mediapipe/tasks-vision";
import type { PoseMetrics } from "../model/detectorTypes";

const POSE = {
  nose: 0,
  leftShoulder: 11,
  rightShoulder: 12,
  leftElbow: 13,
  rightElbow: 14,
  leftWrist: 15,
  rightWrist: 16,
  leftHip: 23,
  rightHip: 24,
} as const;

function average(a: number, b: number) {
  return (a + b) / 2;
}

function distance(a: NormalizedLandmark, b: NormalizedLandmark) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  const dz = (a.z ?? 0) - (b.z ?? 0);

  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

function angleAt(
  vertex: NormalizedLandmark,
  pointA: NormalizedLandmark,
  pointB: NormalizedLandmark,
) {
  const sideA = distance(vertex, pointA);
  const sideB = distance(vertex, pointB);
  const oppositeSide = distance(pointA, pointB);

  if (!sideA || !sideB) {
    return null;
  }

  const cosine =
    (sideA * sideA + sideB * sideB - oppositeSide * oppositeSide) / (2 * sideA * sideB);
  const safeCosine = Math.min(1, Math.max(-1, cosine));
  return (Math.acos(safeCosine) * 180) / Math.PI;
}

function visibilityOf(...points: Array<NormalizedLandmark | undefined>) {
  const visibilities = points
    .map((point) => point?.visibility ?? 0)
    .filter((value) => Number.isFinite(value));

  if (!visibilities.length) {
    return 0;
  }

  return visibilities.reduce((total, value) => total + value, 0) / visibilities.length;
}

export function getPoseMetrics(landmarks: NormalizedLandmark[]): PoseMetrics {
  const nose = landmarks[POSE.nose];
  const leftShoulder = landmarks[POSE.leftShoulder];
  const rightShoulder = landmarks[POSE.rightShoulder];
  const leftElbow = landmarks[POSE.leftElbow];
  const rightElbow = landmarks[POSE.rightElbow];
  const leftWrist = landmarks[POSE.leftWrist];
  const rightWrist = landmarks[POSE.rightWrist];
  const leftHip = landmarks[POSE.leftHip];
  const rightHip = landmarks[POSE.rightHip];

  const shoulderConfidence = visibilityOf(leftShoulder, rightShoulder);
  const elbowConfidence = visibilityOf(leftElbow, rightElbow, leftWrist, rightWrist);
  const hipConfidence = visibilityOf(leftHip, rightHip);
  const noseConfidence = visibilityOf(nose);

  const midShoulderY =
    leftShoulder && rightShoulder ? average(leftShoulder.y, rightShoulder.y) : null;
  const midHipY = leftHip && rightHip ? average(leftHip.y, rightHip.y) : null;

  let headHeight: number | null = null;
  if (nose && midShoulderY !== null && noseConfidence > 0.4) {
    headHeight = midShoulderY - nose.y;
  } else if (midShoulderY !== null && midHipY !== null && hipConfidence > 0.4) {
    headHeight = midHipY - midShoulderY;
  }

  let elbowAngle: number | null = null;
  if (leftShoulder && leftElbow && leftWrist && rightShoulder && rightElbow && rightWrist) {
    const leftAngle = angleAt(leftElbow, leftShoulder, leftWrist);
    const rightAngle = angleAt(rightElbow, rightShoulder, rightWrist);
    if (leftAngle !== null && rightAngle !== null) {
      elbowAngle = average(leftAngle, rightAngle);
    }
  }

  return {
    headHeight,
    elbowAngle,
    shoulderConfidence,
    elbowConfidence,
    confidence: Math.min(shoulderConfidence, elbowConfidence),
  };
}
