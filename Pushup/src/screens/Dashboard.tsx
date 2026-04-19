import TopBar from "../components/TopBar";
import PushupRing from "../components/PushupRing";
import StatCard from "../components/StatCard";
import HeroImage from "../components/HeroImage";
import ProgressChart from "../components/ProgressChart";
import { todayStats, last30Days } from "../data/mock";
import { getLast30DayCounts, getTodayStats } from "../features/pushup-detection";
import { useI18n } from "../i18n";

type DashboardProps = {
  onStartSession: () => void;
  onOpenVideoDebug: () => void;
};

export default function Dashboard({ onStartSession, onOpenVideoDebug }: DashboardProps) {
  const { copy } = useI18n();
  const realTodayStats = getTodayStats();
  const realLast30Days = getLast30DayCounts();
  const ringValue = realTodayStats.pushups || todayStats.pushups;
  const streakValue = realTodayStats.streak || todayStats.streak;
  const chartData = realLast30Days.some((value) => value > 0) ? realLast30Days : last30Days;

  return (
    <div className="flex flex-col">
      <TopBar />
      <PushupRing value={ringValue} goal={realTodayStats.goal} />
      <div className="flex gap-3 px-4 mt-3">
        <StatCard label={copy.dashboard.caloriesBurned} value={`${todayStats.calories}`} unit="kcal" />
        <StatCard label={copy.dashboard.currentStreak} value={`${streakValue}`} unit={copy.dashboard.days} />
      </div>
      <HeroImage />
      <ProgressChart data={chartData} />
      <div className="px-4 mt-4">
        <button
          type="button"
          onClick={onStartSession}
          className="w-full rounded-full bg-gradient-to-r from-[#FF8A3D] to-[#FF6A1A] text-white font-extrabold text-[18px] tracking-[0.04em] py-3.5 shadow-[0_10px_30px_-8px_rgba(255,106,26,0.8)] active:scale-[0.98] transition-transform"
        >
          {copy.dashboard.startSession}
        </button>
        <button
          type="button"
          onClick={onOpenVideoDebug}
          className="mt-3 w-full rounded-full border border-white/14 bg-white/8 py-3 text-[14px] font-semibold text-white/88 backdrop-blur-md active:scale-[0.99] transition-transform"
        >
          Debug Video
        </button>
      </div>
    </div>
  );
}
