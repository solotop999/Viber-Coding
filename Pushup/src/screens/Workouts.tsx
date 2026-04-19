import { Search, Clock } from "lucide-react";
import { workouts } from "../data/mock";
import { useI18n } from "../i18n";

export default function Workouts() {
  const { copy } = useI18n();

  return (
    <div className="flex flex-col">
      <div className="px-5 pt-2 pb-3 flex items-center justify-between">
        <h1 className="text-[20px] font-extrabold">{copy.workouts.title}</h1>
        <button className="w-9 h-9 rounded-full bg-surface border border-border flex items-center justify-center">
          <Search size={15} />
        </button>
      </div>
      <div className="px-4 flex gap-2 overflow-x-auto no-scrollbar pb-2">
        {copy.workouts.categories.map((category, i) => (
          <button
            key={category}
            className={`px-3 py-1.5 rounded-full text-[11px] font-semibold border ${
              i === 0
                ? "bg-primary text-white border-primary"
                : "bg-surface text-muted border-border"
            }`}
          >
            {category}
          </button>
        ))}
      </div>
      <div className="px-4 mt-2 flex flex-col gap-2.5">
        {workouts.map((workout) => {
          const title = copy.workouts.titles[workout.title] ?? workout.title;
          const subtitle = copy.workouts.subtitles[workout.id] ?? workout.subtitle;
          const level = copy.workouts.levels[workout.level as "Easy" | "Medium" | "Hard"];

          return (
            <div
              key={workout.id}
              className="rounded-2xl bg-surface border border-border/60 p-3 flex items-center gap-3"
            >
              <div
                className="w-12 h-12 rounded-xl shrink-0 flex items-center justify-center font-extrabold text-white text-[16px]"
                style={{
                  background: `linear-gradient(135deg, ${workout.color}, ${workout.color}99)`,
                }}
              >
                {title[0]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-bold text-[14px]">{title}</div>
                <div className="text-[11px] text-muted">{subtitle}</div>
                <div className="flex items-center gap-1 mt-0.5 text-[10px] text-muted">
                  <Clock size={10} />
                  {workout.minutes} {copy.workouts.minutes} · {level}
                </div>
              </div>
              <button className="px-3 py-1.5 rounded-full bg-primary/15 text-primary text-[11px] font-bold">
                {copy.workouts.start}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
