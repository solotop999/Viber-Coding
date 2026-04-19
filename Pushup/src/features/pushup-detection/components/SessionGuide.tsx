import type { DetectorPhase, DetectorStatus } from "../model/detectorTypes";

type SessionGuideProps = {
  message: string;
  status: DetectorStatus;
  phase: DetectorPhase;
  calibrationProgress: number;
  confidence: number;
};

function statusLabel(status: DetectorStatus, phase: DetectorPhase) {
  switch (status) {
    case "requesting_camera":
      return "CHUẨN BỊ CAMERA";
    case "countdown":
      return "SẮP BẮT ĐẦU";
    case "tracking":
      return phase === "unknown" ? "SẴN SÀNG" : "ĐANG THEO DÕI";
    case "paused":
      return "ĐÃ TẠM DỪNG";
    case "error":
      return "CÓ LỖI XẢY RA";
    case "finished":
      return "HOÀN TẤT";
    default:
      return "SẴN SÀNG";
  }
}

function nextAction(status: DetectorStatus, phase: DetectorPhase, fallback: string) {
  if (status === "tracking" && phase !== "unknown") {
    switch (phase) {
      case "up":
      case "going_down":
        return "Hạ người xuống chậm và sâu hơn";
      case "down":
      case "going_up":
        return "Đẩy mạnh người lên về đỉnh";
      default:
        return fallback;
    }
  }

  return fallback;
}

function helperText(status: DetectorStatus, phase: DetectorPhase) {
  switch (status) {
    case "requesting_camera":
      return "Cho phép truy cập camera và đặt điện thoại cố định trước khi bắt đầu.";
    case "countdown":
      return "Vào tư thế chống đẩy ban đầu và chờ đếm ngược kết thúc.";
    case "tracking":
      return phase === "unknown"
        ? "Ứng dụng đang đợi bạn bắt đầu nhịp đầu tiên."
        : "Thực hiện trọn một nhịp xuống và lên để được tính rep.";
    case "paused":
      return "Quay lại ứng dụng để tiếp tục buổi tập.";
    case "error":
      return "Kiểm tra quyền camera hoặc tải lại trang rồi thử lại.";
    case "finished":
      return "Buổi tập đã kết thúc. Bạn có thể quay lại để xem lịch sử.";
    default:
      return "Đưa cơ thể vào khung hình và bắt đầu hít đất.";
  }
}

export default function SessionGuide({
  message,
  status,
  phase,
  calibrationProgress,
  confidence,
}: SessionGuideProps) {
  const normalizedConfidence = Math.max(0, Math.min(1, confidence));
  const progressValue =
    status === "tracking"
      ? Math.max(0.15, normalizedConfidence)
      : status === "countdown"
        ? 0.2
        : Math.max(0, Math.min(1, calibrationProgress));

  return (
    <div className="w-full max-w-[360px] text-center text-white [text-shadow:0_2px_18px_rgba(0,0,0,0.75)]">
      <div className="text-[11px] font-semibold uppercase tracking-[0.28em] text-white/70">
        {statusLabel(status, phase)}
      </div>
      <div className="mt-2 text-[24px] font-black tracking-[-0.03em] text-white">
        {nextAction(status, phase, message)}
      </div>
      <div className="mt-2 text-[13px] leading-5 text-white/82">{helperText(status, phase)}</div>

      <div className="mx-auto mt-4 w-full max-w-[300px]">
        <div className="h-[6px] overflow-hidden rounded-full bg-white/16">
          <div
            className="h-full rounded-full bg-[linear-gradient(90deg,#ff4d4f_0%,#ffd166_52%,#29d67d_100%)] transition-[width] duration-300"
            style={{ width: `${progressValue * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
