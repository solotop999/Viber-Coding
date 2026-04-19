import { LayoutGrid, Dumbbell, Clock, User } from "lucide-react";
import type { TabKey } from "../types";

const tabs: { key: TabKey; label: string; Icon: typeof LayoutGrid }[] = [
  { key: "dashboard", label: "Dashboard", Icon: LayoutGrid },
  { key: "workouts", label: "Workouts", Icon: Dumbbell },
  { key: "history", label: "History", Icon: Clock },
  { key: "profile", label: "Profile", Icon: User },
];

type Props = { active: TabKey; onChange: (t: TabKey) => void };

export default function BottomTabBar({ active, onChange }: Props) {
  return (
    <div className="absolute bottom-0 inset-x-0 pb-3 pt-2 bg-bg/80 backdrop-blur-md border-t border-border/50">
      <div className="flex items-center justify-around px-2">
        {tabs.map(({ key, label, Icon }) => {
          const isActive = key === active;
          return (
            <button
              key={key}
              onClick={() => onChange(key)}
              className="flex flex-col items-center gap-0.5 py-1 px-2"
            >
              <Icon
                size={18}
                className={isActive ? "text-primary" : "text-muted"}
                strokeWidth={isActive ? 2.5 : 2}
              />
              <span
                className={`text-[9px] font-semibold ${
                  isActive ? "text-primary" : "text-muted"
                }`}
              >
                {label}
              </span>
            </button>
          );
        })}
      </div>
      <div className="mt-1 mx-auto w-[35%] h-[4px] rounded-full bg-text/80" />
    </div>
  );
}
