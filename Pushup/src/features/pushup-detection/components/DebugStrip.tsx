import { useState } from "react";
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

function getMotionLabel(frame: DetectorFrameState) {
  if (!frame.debug.readyToCount) {
    return "Chờ sẵn sàng";
  }

  switch (frame.debug.motionTrend) {
    case "falling":
      return "Đang xuống";
    case "rising":
      return "Đang lên";
    case "steady":
      return "Đứng yên";
    default:
      return "Khó xác định";
  }
}

function getHeightZoneLabel(frame: DetectorFrameState) {
  if (!frame.debug.readyToCount) {
    return "Chưa đếm";
  }

  const current = frame.debug.smoothedMotionSignal;
  const top = frame.upThreshold;
  const bottom = frame.downThreshold;

  if (current === null || top === null || bottom === null) {
    return "Khó xác định";
  }

  if (current >= top) {
    return "Đang ở trên cao";
  }

  if (current <= bottom) {
    return "Đang ở dưới thấp";
  }

  return "Đang ở giữa";
}

function getReadyLabel(frame: DetectorFrameState) {
  if (frame.debug.readyToCount) {
    return "Đã sẵn sàng";
  }

  return "Đang canh tư thế";
}

function getHintLabel(frame: DetectorFrameState) {
  switch (frame.debug.repBlockReason) {
    case "waiting_for_ready":
      return frame.message;
    case "low_confidence":
      return "Giữ 2 vai rõ hơn";
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

  const confidencePercent = Math.round(frame.confidence * 100);
  const positionScore = getPositionScore(frame);
  const debugText = [
    `Trạng thái sẵn sàng: ${getReadyLabel(frame)}`,
    `Tiến độ sẵn sàng: ${Math.round(frame.debug.readyProgress * 100)}%`,
    `Số rep: ${frame.repCount}`,
    `Hướng hiện tại: ${getMotionLabel(frame)}`,
    `Mức cao/thấp hiện tại: ${getHeightZoneLabel(frame)}`,
    `Thang cao/thấp: ${positionScore ? `${positionScore}/10` : "--"}`,
    `Độ cao đầu hiện tại: ${formatValue(frame.debug.smoothedMotionSignal)}`,
    `Mốc trên để coi là ở cao: ${formatValue(frame.upThreshold)}`,
    `Mốc dưới để coi là ở thấp: ${formatValue(frame.downThreshold)}`,
    `Độ tin cậy tracking: ${confidencePercent}%`,
    `Gợi ý: ${getHintLabel(frame)}`,
  ].join("\n");

  if (!visible) {
    return null;
  }

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
    <div className="max-w-[min(88vw,520px)] px-1 py-1 text-white/95 select-text [text-shadow:0_2px_10px_rgba(0,0,0,0.95)]">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div className="text-[12px] font-semibold uppercase tracking-[0.16em] text-white/75">
          Debug
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="pointer-events-auto rounded-full border border-white/30 px-3 py-1 text-[12px] font-semibold text-white/95"
        >
          {copied ? "Đã copy" : "Copy"}
        </button>
      </div>

      <pre className="whitespace-pre-wrap break-words font-mono text-[14px] leading-7 text-white">
        {debugText}
      </pre>

      <div className="mt-3">
        <div className="h-2 overflow-hidden rounded-full bg-white/20">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[#FF6A1A] via-[#FFD166] to-[#73FFA8]"
            style={{ width: `${Math.max(0, Math.min(100, confidencePercent))}%` }}
          />
        </div>
      </div>
    </div>
  );
}
