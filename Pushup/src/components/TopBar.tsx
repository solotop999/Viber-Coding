import { User, Flame } from "lucide-react";

export default function TopBar() {
  return (
    <div className="flex items-center justify-between px-5 pt-2 pb-3">
      <div className="flex items-center gap-1.5">
        <Flame size={20} className="text-primary" fill="#FF6A1A" />
        <span
          style={{
            fontFamily: "Oswald, Inter, sans-serif",
            fontWeight: 700,
            fontStyle: "italic",
            fontSize: 22,
            letterSpacing: "0.01em",
            lineHeight: 1,
          }}
        >
          <span style={{ color: "#FF6A1A" }}>PUSH</span>
          <span style={{ color: "#F5F5F5", marginLeft: 4 }}>UP</span>
        </span>
      </div>
      <button className="w-9 h-9 rounded-full bg-surface border border-border flex items-center justify-center">
        <User size={16} className="text-text" />
      </button>
    </div>
  );
}
