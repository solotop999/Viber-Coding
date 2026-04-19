import { Calendar, Flame, Clock } from "lucide-react";
import { history, last30Days } from "../data/mock";
import { getRecentHistory, getWeeklyHistorySummary } from "../features/pushup-detection";
import { useI18n } from "../i18n";

export default function History() {
  const { copy } = useI18n();
  const summary = getWeeklyHistorySummary();
  const recentHistory = getRecentHistory();
  const total = summary.total || history.reduce((a, b) => a + b.reps, 0);
  const avg = summary.average || Math.round(total / history.length);
  const chart = summary.chart.some((value) => value > 0) ? summary.chart : last30Days.slice(-7);
  const items =
    recentHistory.length > 0
      ? recentHistory.map((session) => ({
          id: session.id,
          monthLabel: session.monthLabel,
          dayLabel: session.dayLabel,
          reps: session.repCount,
          minutes: session.minutesLabel,
        }))
      : history.map((item) => ({
          id: item.date,
          monthLabel: item.date.split(" ")[0],
          dayLabel: item.date.split(" ")[1],
          reps: item.reps,
          minutes: item.minutes.toString(),
        }));

  return (
    <div className="flex flex-col">
      <div className="px-5 pt-2 pb-3 flex items-center justify-between">
        <h1 className="text-[20px] font-extrabold">{copy.history.title}</h1>
        <button className="w-9 h-9 rounded-full bg-surface border border-border flex items-center justify-center">
          <Calendar size={15} />
        </button>
      </div>

      <div className="mx-4 rounded-2xl bg-surface border border-border/60 p-4">
        <div className="text-[10px] tracking-[0.2em] text-muted font-semibold">
          {copy.history.thisWeek}
        </div>
        <div className="flex items-end gap-3 mt-2">
          <div>
            <div className="text-[28px] font-extrabold leading-none">{total}</div>
            <div className="text-[10px] text-muted mt-1">{copy.history.totalReps}</div>
          </div>
          <div className="ml-auto text-right">
            <div className="text-[14px] font-bold text-primary">{avg}/day</div>
            <div className="text-[10px] text-muted">{copy.history.average}</div>
          </div>
        </div>
        <div className="mt-3 flex items-end gap-[3px] h-[36px]">
          {chart.map((v, i) => {
            const max = Math.max(...chart, 1);
            return (
              <div
                key={i}
                className="flex-1 rounded-[2px]"
                style={{
                  height: `${(v / max) * 100}%`,
                  background: i === 6 ? "#FF6A1A" : "#3a3a40",
                }}
              />
            );
          })}
        </div>
      </div>

      <div className="px-4 mt-3">
        <div className="text-[10px] tracking-[0.2em] text-muted font-semibold mb-2">
          {copy.history.recentSessions}
        </div>
        <div className="flex flex-col gap-2">
          {items.map((h) => (
            <div
              key={h.id}
              className="rounded-2xl bg-surface border border-border/60 px-3 py-2.5 flex items-center gap-3"
            >
              <div className="w-10 h-10 rounded-xl bg-primary/15 flex flex-col items-center justify-center">
                <span className="text-[9px] text-muted font-semibold leading-none">
                  {h.monthLabel}
                </span>
                <span className="text-[14px] font-extrabold text-primary leading-none mt-0.5">
                  {h.dayLabel}
                </span>
              </div>
              <div className="flex-1">
                <div className="font-bold text-[14px]">{h.reps} {copy.history.pushups}</div>
                <div className="flex items-center gap-2 text-[10px] text-muted mt-0.5">
                  <span className="flex items-center gap-0.5">
                    <Flame size={10} /> -- kcal
                  </span>
                  <span className="flex items-center gap-0.5">
                    <Clock size={10} /> {h.minutes}m
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
