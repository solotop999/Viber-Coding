import { FilesetResolver, PoseLandmarker } from "@mediapipe/tasks-vision";
import { MEDIAPIPE_WASM_BASE_URL, POSE_MODEL_ASSET_URL } from "../model/constants";

let poseLandmarkerPromise: Promise<PoseLandmarker> | null = null;

async function createPoseLandmarker(delegate: "GPU" | "CPU") {
  const vision = await FilesetResolver.forVisionTasks(MEDIAPIPE_WASM_BASE_URL);
  const canvas = document.createElement("canvas");

  return PoseLandmarker.createFromOptions(vision, {
    baseOptions: {
      delegate,
      modelAssetPath: POSE_MODEL_ASSET_URL,
    },
    canvas,
    runningMode: "VIDEO",
    numPoses: 1,
    minPoseDetectionConfidence: 0.5,
    minPosePresenceConfidence: 0.5,
    minTrackingConfidence: 0.5,
  });
}

export async function loadPoseLandmarker() {
  if (!poseLandmarkerPromise) {
    poseLandmarkerPromise = createPoseLandmarker("GPU").catch(() => createPoseLandmarker("CPU"));
  }

  return poseLandmarkerPromise;
}

export function resetPoseLandmarker() {
  poseLandmarkerPromise = null;
}
