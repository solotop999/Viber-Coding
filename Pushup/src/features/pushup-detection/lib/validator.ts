type ValidationOptions = {
  confidence: number;
  confidenceThreshold: number;
  elapsedMs: number;
  minRepDurationMs: number;
  maxRepDurationMs: number;
};

export function hasEnoughConfidence(confidence: number, threshold: number) {
  return confidence >= threshold;
}

export function isRepDurationValid({
  confidence,
  confidenceThreshold,
  elapsedMs,
  minRepDurationMs,
  maxRepDurationMs,
}: ValidationOptions) {
  if (!hasEnoughConfidence(confidence, confidenceThreshold)) {
    return false;
  }

  return elapsedMs >= minRepDurationMs && elapsedMs <= maxRepDurationMs;
}
