import { LayoutGrid, Dumbbell, Clock, User } from "lucide-react";
import type { TabKey } from "../types";
import { useI18n } from "../i18n";

const tabs: { key: TabKey; Icon: typeof LayoutGrid }[] = [
  { key: "dashboard", Icon: LayoutGrid },
  { key: "workouts", Icon: Dumbbell },
  { key: "history", Icon: Clock },
  { key: "profile", Icon: User },
];

type Props = { active: TabKey; onChange: (t: TabKey) => void };

export default function BottomTabBar({ active, onChange }: Props) {
  const { copy } = useI18n();

  return (
    <div className="absolute bottom-0 inset-x-0 pb-3 pt-2 bg-bg/80 backdrop-blur-md border-t border-border/50">
      <div className="flex items-center justify-around px-2">
        {tabs.map(({ key, Icon }) => {
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
                {copy.tabs[key]}
              </span>
            </button>
          );
        })}
      </div>
      <div className="mt-1 mx-auto w-[35%] h-[4px] rounded-full bg-text/80" />
    </div>
  );
}
