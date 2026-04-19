import { Flame } from "lucide-react";

type Props = { label: string; value: string; unit: string };

export default function StatCard({ label, value, unit }: Props) {
  return (
    <div className="flex-1 rounded-2xl bg-surface border border-border/60 px-3 py-3 flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-primary/15 flex items-center justify-center shrink-0">
        <Flame size={18} className="text-primary" fill="#FF6A1A" />
      </div>
      <div className="min-w-0 flex flex-col">
        <span
          style={{
            fontSize: 11,
            color: "#8A8A90",
            fontWeight: 500,
            lineHeight: 1.2,
          }}
        >
          {label}
        </span>
        <span style={{ marginTop: 2, lineHeight: 1 }}>
          <span
            style={{
              fontFamily: "Oswald, Inter, sans-serif",
              fontSize: 22,
              fontWeight: 700,
              color: "#F5F5F5",
              letterSpacing: "-0.01em",
            }}
          >
            {value}
          </span>
          <span
            style={{
              marginLeft: 4,
              fontSize: 11,
              color: "#8A8A90",
              fontWeight: 500,
            }}
          >
            {unit}
          </span>
        </span>
      </div>
    </div>
  );
}
