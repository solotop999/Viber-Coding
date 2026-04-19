import TopBar from "../components/TopBar";
import PushupRing from "../components/PushupRing";
import StatCard from "../components/StatCard";
import HeroImage from "../components/HeroImage";
import ProgressChart from "../components/ProgressChart";
import { todayStats, last30Days } from "../data/mock";
import { useI18n } from "../i18n";

export default function Dashboard() {
  const { copy } = useI18n();

  return (
    <div className="flex flex-col">
      <TopBar />
      <PushupRing value={todayStats.pushups} goal={todayStats.goal} />
      <div className="flex gap-3 px-4 mt-3">
        <StatCard label={copy.dashboard.caloriesBurned} value={`${todayStats.calories}`} unit="kcal" />
        <StatCard label={copy.dashboard.currentStreak} value={`${todayStats.streak}`} unit={copy.dashboard.days} />
      </div>
      <HeroImage />
      <ProgressChart data={last30Days} />
      <div className="px-4 mt-4">
        <button className="w-full rounded-full bg-gradient-to-r from-[#FF8A3D] to-[#FF6A1A] text-white font-extrabold text-[18px] tracking-[0.04em] py-3.5 shadow-[0_10px_30px_-8px_rgba(255,106,26,0.8)] active:scale-[0.98] transition-transform">
          {copy.dashboard.startSession}
        </button>
      </div>
    </div>
  );
}
