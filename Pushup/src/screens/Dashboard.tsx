import TopBar from "../components/TopBar";
import PushupRing from "../components/PushupRing";
import StatCard from "../components/StatCard";
import HeroImage from "../components/HeroImage";
import ProgressChart from "../components/ProgressChart";
import { todayStats, last30Days } from "../data/mock";

export default function Dashboard() {
  return (
    <div className="flex flex-col">
      <TopBar />
      <PushupRing value={todayStats.pushups} goal={todayStats.goal} />
      <div className="flex gap-3 px-4 mt-3">
        <StatCard label="Calories Burned" value={`${todayStats.calories}`} unit="kcal" />
        <StatCard label="Current Streak" value={`${todayStats.streak}`} unit="Days" />
      </div>
      <HeroImage />
      <ProgressChart data={last30Days} />
      <div className="px-4 mt-4">
        <button className="w-full rounded-full bg-gradient-to-r from-[#FF8A3D] to-[#FF6A1A] text-white font-bold text-[14px] py-3.5 shadow-[0_10px_30px_-8px_rgba(255,106,26,0.8)] active:scale-[0.98] transition-transform">
          START SESSION
        </button>
      </div>
    </div>
  );
}
