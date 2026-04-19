import { Signal, Wifi, BatteryFull } from "lucide-react";

export default function StatusBar() {
  return (
    <div className="relative z-40 flex items-center justify-between px-7 pt-3 pb-1 text-[13px] font-semibold">
      <span>9:41</span>
      <div className="flex items-center gap-1.5">
        <Signal size={14} strokeWidth={2.5} />
        <Wifi size={14} strokeWidth={2.5} />
        <BatteryFull size={18} strokeWidth={2.5} />
      </div>
    </div>
  );
}
