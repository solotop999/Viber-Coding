import type { DetectorFrameState } from "../model/detectorTypes";

type DebugStripProps = {
  frame: DetectorFrameState;
  visible: boolean;
};

function formatValue(value: number | null) {
  if (value === null) {
    return "--";
  }

  return value.toFixed(3);
}

function formatDuration(value: number | null) {
  if (value === null || !Number.isFinite(value)) {
    return "--";
  }

  return `${Math.round(value)}ms`;
}

export default function DebugStrip({ frame, visible }: DebugStripProps) {
  if (!visible) {
    return null;
  }

  const confidencePercent = Math.round(frame.confidence * 100);

  return (
    <div className="rounded-2xl border border-white/10 bg-black/45 px-3 py-2 text-[11px] text-white/80 backdrop-blur-md">
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        <span>Trạng thái: {frame.status}</span>
        <span>Pha: {frame.phase}</span>
        <span>FPS: {frame.fps}</span>
        <span>Tin cậy: {formatValue(frame.confidence)}</span>
        <span>Head raw: {formatValue(frame.debug.rawHeadHeight)}</span>
        <span>Head mượt: {formatValue(frame.debug.smoothedHeadHeight)}</span>
        <span>Elbow raw: {formatValue(frame.debug.rawElbowAngle)}</span>
        <span>Elbow mượt: {formatValue(frame.debug.smoothedElbowAngle)}</span>
        <span>Nền: {formatValue(frame.baseline)}</span>
        <span>Ngưỡng lên: {formatValue(frame.upThreshold)}</span>
        <span>Ngưỡng xuống: {formatValue(frame.downThreshold)}</span>
        <span>Hiệu chỉnh: {Math.round(frame.calibrationProgress * 100)}%</span>
        <span>Chuyển pha: {frame.debug.transitionFrom} -&gt; {frame.debug.transitionTo}</span>
        <span>Tạm block: {frame.debug.repBlockReason}</span>
        <span>Đã chạm đáy: {frame.debug.reachedBottom ? "yes" : "no"}</span>
        <span>Rep event: {frame.debug.transitionCompletedRep ? "yes" : "no"}</span>
        <span>Ngưỡng calib: {formatValue(frame.debug.calibrationMinAngle)}</span>
        <span>Frame vào calib: {frame.debug.calibrationAcceptedFrame ? "yes" : "no"}</span>
        <span>Thời gian rep: {formatDuration(frame.debug.elapsedMsSinceLastRep)}</span>
        <span>
          Min/Max: {formatDuration(frame.debug.minRepDurationMs)} /{" "}
          {formatDuration(frame.debug.maxRepDurationMs)}
        </span>
      </div>
      <div className="mt-2">
        <div className="mb-1 flex items-center justify-between text-[10px] text-white/55">
          <span>Độ tin cậy theo dõi</span>
          <span>{confidencePercent}%</span>
        </div>
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
