import { X } from "lucide-react";

type SessionHudProps = {
  elapsedSec: number;
  repCount: number;
  onClose: () => void;
};

function formatTime(value: number) {
  const minutes = Math.floor(value / 60)
    .toString()
    .padStart(2, "0");
  const seconds = Math.floor(value % 60)
    .toString()
    .padStart(2, "0");

  return `${minutes}:${seconds}`;
}

export default function SessionHud({ elapsedSec, repCount, onClose }: SessionHudProps) {
  return (
    <div className="pointer-events-none absolute inset-0 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="rounded-full border border-white/10 bg-black/35 px-4 py-2 text-[12px] font-semibold text-white/80 backdrop-blur-md">
          {formatTime(elapsedSec)}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="pointer-events-auto flex h-11 w-11 items-center justify-center rounded-full border border-white/10 bg-black/35 text-white backdrop-blur-md"
        >
          <X size={18} />
        </button>
      </div>

      <div className="pointer-events-none absolute inset-x-0 top-[15%] text-center">
        <div className="text-[13px] font-semibold uppercase tracking-[0.32em] text-[#ffd7bf] [text-shadow:0_3px_18px_rgba(0,0,0,0.7)]">
          Hít đất
        </div>
        <div className="mt-2 text-[118px] font-black leading-none tracking-[-0.08em] text-[#FF6A1A] [text-shadow:0_8px_30px_rgba(255,106,26,0.38)]">
          {repCount}
        </div>
      </div>
    </div>
  );
}
