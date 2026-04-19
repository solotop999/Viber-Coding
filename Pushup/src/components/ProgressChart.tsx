import { ChevronRight } from "lucide-react";
import { useI18n } from "../i18n";

type Props = { data: number[] };

export default function ProgressChart({ data }: Props) {
  const { copy } = useI18n();
  const max = Math.max(...data);
  const highlight = data.indexOf(max);
  return (
    <div
      className="mx-4 mt-3 rounded-2xl border border-border/60 px-4 pt-3 pb-3"
      style={{ backgroundColor: "rgba(0, 0, 0, 0.69)" }}
    >
      <div className="flex items-center justify-between">
        <span className="text-[13px] tracking-[0.08em] text-white font-bold">
          {copy.dashboard.progress30Day}
        </span>
        <button className="flex items-center gap-0.5 text-[11px] text-primary font-semibold">
          {copy.dashboard.barChart} <ChevronRight size={12} />
        </button>
      </div>
      <div className="mt-3 flex items-end gap-[3px] h-[56px]">
        {data.map((v, i) => {
          const h = (v / max) * 100;
          const isHi = i === highlight;
          return (
            <div
              key={i}
              className="flex-1 rounded-[2px] transition-colors"
              style={{
                height: `${h}%`,
                background: isHi ? "#FF6A1A" : "#3a3a40",
                boxShadow: isHi ? "0 0 8px rgba(255,106,26,0.6)" : undefined,
              }}
            />
          );
        })}
      </div>
      <div className="flex justify-between text-[9px] text-muted mt-1 font-medium">
        <span>1</span><span>10</span><span>20</span><span>30</span>
      </div>
    </div>
  );
}
