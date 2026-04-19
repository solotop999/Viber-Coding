import { Settings, Award, Target, Zap, ChevronRight } from "lucide-react";
import { user, achievements, todayStats } from "../data/mock";
import { useI18n } from "../i18n";

export default function Profile() {
  const { copy } = useI18n();
  const xpPct = (user.xp / user.xpToNext) * 100;

  return (
    <div className="flex flex-col">
      <div className="px-5 pt-2 pb-3 flex items-center justify-between">
        <h1 className="text-[20px] font-extrabold">{copy.profile.title}</h1>
        <button className="w-9 h-9 rounded-full bg-surface border border-border flex items-center justify-center">
          <Settings size={15} />
        </button>
      </div>

      <div className="mx-4 rounded-2xl bg-surface border border-border/60 p-4 flex items-center gap-3 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_20%,rgba(255,106,26,0.18),transparent_50%)] pointer-events-none" />
        <div className="w-14 h-14 rounded-full bg-gradient-to-br from-[#FF8A3D] to-[#FF6A1A] flex items-center justify-center font-extrabold text-white text-[20px] shrink-0">
          {user.name[0]}
        </div>
        <div className="flex-1 min-w-0 relative">
          <div className="font-extrabold text-[15px]">{user.name}</div>
          <div className="text-[11px] text-muted">{user.handle} · {copy.profile.joined} {user.joined}</div>
        </div>
        <div className="text-right relative">
          <div className="text-[10px] text-muted font-semibold">{copy.profile.level}</div>
          <div className="text-[22px] font-extrabold text-primary leading-none">
            {user.level}
          </div>
        </div>
      </div>

      <div className="mx-4 mt-3 rounded-2xl bg-surface border border-border/60 p-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-muted font-semibold">{copy.profile.xpProgress}</span>
          <span className="text-[11px] font-bold">
            {user.xp}<span className="text-muted">/{user.xpToNext}</span>
          </span>
        </div>
        <div className="mt-2 h-2 rounded-full bg-border overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#FF8A3D] to-[#FF6A1A]"
            style={{ width: `${xpPct}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 px-4 mt-3">
        <StatBox icon={Target} label={copy.profile.goal} value={`${todayStats.goal}`} />
        <StatBox icon={Zap} label={copy.profile.streak} value={`${todayStats.streak}d`} />
        <StatBox
          icon={Award}
          label={copy.profile.badges}
          value={`${achievements.filter((a) => a.unlocked).length}`}
        />
      </div>

      <div className="px-4 mt-3">
        <div className="text-[10px] tracking-[0.2em] text-muted font-semibold mb-2">
          {copy.profile.achievements}
        </div>
        <div className="flex flex-col gap-2">
          {achievements.map((a) => (
            <div
              key={a.id}
              className={`rounded-2xl bg-surface border border-border/60 px-3 py-2.5 flex items-center gap-3 ${
                !a.unlocked ? "opacity-50" : ""
              }`}
            >
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                  a.unlocked ? "bg-primary/15" : "bg-border"
                }`}
              >
                <Award size={16} className={a.unlocked ? "text-primary" : "text-muted"} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-bold text-[13px]">{copy.profile.achievementTitles[a.title] ?? a.title}</div>
                <div className="text-[10px] text-muted">{copy.profile.achievementDescs[a.desc] ?? a.desc}</div>
              </div>
              <ChevronRight size={14} className="text-muted" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatBox({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Target;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl bg-surface border border-border/60 p-3 flex flex-col items-center">
      <Icon size={16} className="text-primary" />
      <div className="text-[16px] font-extrabold mt-1">{value}</div>
      <div className="text-[9px] text-muted font-semibold">{label}</div>
    </div>
  );
}
