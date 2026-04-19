import { useMemo, useState } from "react";
import type { DetectorFrameState } from "../model/detectorTypes";

type DebugStripProps = {
  frame: DetectorFrameState;
  visible: boolean;
};

function formatValue(value: number | null) {
  if (value === null || !Number.isFinite(value)) {
    return "--";
  }

  return value.toFixed(3);
}

function getPositionScore(frame: DetectorFrameState) {
  const current = frame.debug.smoothedMotionSignal;
  const top = frame.upThreshold;
  const bottom = frame.downThreshold;

  if (current === null || top === null || bottom === null || bottom === top) {
    return null;
  }

  const min = Math.min(top, bottom);
  const max = Math.max(top, bottom);
  const normalized = (current - min) / (max - min);
  const clamped = Math.max(0, Math.min(1, normalized));

  return Math.round(clamped * 9) + 1;
}

function getPositionLabel(frame: DetectorFrameState) {
  switch (frame.phase) {
    case "up":
      return "Cao nhất";
    case "going_down":
      return "Đang xuống";
    case "down":
      return "Thấp nhất";
    case "going_up":
      return "Đang lên";
    default:
      return frame.debug.active ? "Đang theo dõi" : "Chưa bắt đầu";
  }
}

function getReadyLabel(frame: DetectorFrameState) {
  if (frame.debug.active) {
    return "Đã sẵn sàng";
  }

  return "Đang đợi bắt đầu";
}

function getHintLabel(frame: DetectorFrameState) {
  switch (frame.debug.repBlockReason) {
    case "waiting_for_activation":
      return "Làm 1 nhịp rõ để bắt đầu đếm";
    case "waiting_for_bottom":
      return "Xuống sâu thêm";
    case "waiting_for_full_extension":
      return "Lên cao thêm";
    case "low_confidence":
      return "Giữ vai và tay rõ hơn";
    case "duration_too_short":
      return "Đừng làm quá nhanh";
    case "duration_too_long":
      return "Giữ nhịp đều hơn";
    default:
      return "Đang ổn";
  }
}

export default function DebugStrip({ frame, visible }: DebugStripProps) {
  const [copied, setCopied] = useState(false);

  if (!visible) {
    return null;
  }

  const confidencePercent = Math.round(frame.confidence * 100);
  const positionScore = getPositionScore(frame);

  const debugText = useMemo(
    () =>
      [
        `San sang: ${getReadyLabel(frame)}`,
        `Rep: ${frame.repCount}`,
        `Vi tri: ${getPositionLabel(frame)}`,
        `Thang vi tri: ${positionScore ? `${positionScore}/10` : "--"}`,
        `Tracking / Len: ${formatValue(frame.debug.smoothedMotionSignal)} / ${formatValue(frame.upThreshold)}`,
        `Tracking / Xuong: ${formatValue(frame.debug.smoothedMotionSignal)} / ${formatValue(frame.downThreshold)}`,
        `Tin cay: ${confidencePercent}%`,
        `Goi y: ${getHintLabel(frame)}`,
      ].join("\n"),
    [confidencePercent, frame, positionScore],
  );

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(debugText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-black/45 px-3 py-3 text-[12px] text-white/85 backdrop-blur-md select-text">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-white/60">
          Debug
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="pointer-events-auto rounded-full border border-white/12 bg-white/8 px-3 py-1 text-[11px] font-semibold text-white/85"
        >
          {copied ? "Da copy" : "Copy"}
        </button>
      </div>

      <pre className="whitespace-pre-wrap break-words font-mono text-[12px] leading-6 text-white/90">
        {debugText}
      </pre>

      <div className="mt-3">
        <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[#FF6A1A] via-[#FFD166] to-[#73FFA8]"
            style={{ width: `${Math.max(0, Math.min(100, confidencePercent))}%` }}
          />
        </div>
      </div>
    </div>
  );
}
