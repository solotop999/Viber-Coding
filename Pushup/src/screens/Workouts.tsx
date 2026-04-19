import { Search, Clock } from "lucide-react";
import { workouts } from "../data/mock";

export default function Workouts() {
  return (
    <div className="flex flex-col">
      <div className="px-5 pt-2 pb-3 flex items-center justify-between">
        <h1 className="text-[20px] font-extrabold">Workouts</h1>
        <button className="w-9 h-9 rounded-full bg-surface border border-border flex items-center justify-center">
          <Search size={15} />
        </button>
      </div>
      <div className="px-4 flex gap-2 overflow-x-auto no-scrollbar pb-2">
        {["All", "Easy", "Medium", "Hard"].map((c, i) => (
          <button
            key={c}
            className={`px-3 py-1.5 rounded-full text-[11px] font-semibold border ${
              i === 0
                ? "bg-primary text-white border-primary"
                : "bg-surface text-muted border-border"
            }`}
          >
            {c}
          </button>
        ))}
      </div>
      <div className="px-4 mt-2 flex flex-col gap-2.5">
        {workouts.map((w) => (
          <div
            key={w.id}
            className="rounded-2xl bg-surface border border-border/60 p-3 flex items-center gap-3"
          >
            <div
              className="w-12 h-12 rounded-xl shrink-0 flex items-center justify-center font-extrabold text-white text-[16px]"
              style={{
                background: `linear-gradient(135deg, ${w.color}, ${w.color}99)`,
              }}
            >
              {w.title[0]}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-bold text-[14px]">{w.title}</div>
              <div className="text-[11px] text-muted">{w.subtitle}</div>
              <div className="flex items-center gap-1 mt-0.5 text-[10px] text-muted">
                <Clock size={10} />
                {w.minutes} min · {w.level}
              </div>
            </div>
            <button className="px-3 py-1.5 rounded-full bg-primary/15 text-primary text-[11px] font-bold">
              Start
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
