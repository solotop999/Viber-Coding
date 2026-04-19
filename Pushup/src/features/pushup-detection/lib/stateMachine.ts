import type { DetectorPhase } from "../model/detectorTypes";

type TransitionInput = {
  signal: number;
  upThreshold: number;
  downThreshold: number;
};

export function advancePhase(current: DetectorPhase, input: TransitionInput) {
  const { signal, upThreshold, downThreshold } = input;

  switch (current) {
    case "unknown":
      if (signal >= upThreshold) {
        return { nextPhase: "up" as const, completedRep: false };
      }
      if (signal <= downThreshold) {
        return { nextPhase: "down" as const, completedRep: false };
      }
      return { nextPhase: "unknown" as const, completedRep: false };

    case "up":
      if (signal <= upThreshold) {
        return { nextPhase: "going_down" as const, completedRep: false };
      }
      return { nextPhase: "up" as const, completedRep: false };

    case "going_down":
      if (signal <= downThreshold) {
        return { nextPhase: "down" as const, completedRep: false };
      }
      if (signal > upThreshold) {
        return { nextPhase: "up" as const, completedRep: false };
      }
      return { nextPhase: "going_down" as const, completedRep: false };

    case "down":
      if (signal >= downThreshold) {
        return { nextPhase: "going_up" as const, completedRep: false };
      }
      return { nextPhase: "down" as const, completedRep: false };

    case "going_up":
      if (signal > upThreshold) {
        return { nextPhase: "up" as const, completedRep: true };
      }
      if (signal < downThreshold) {
        return { nextPhase: "down" as const, completedRep: false };
      }
      return { nextPhase: "going_up" as const, completedRep: false };
  }
}
