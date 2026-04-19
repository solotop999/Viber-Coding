import { Flame } from "lucide-react";

type Props = { label: string; value: string; unit: string };

export default function StatCard({ label, value, unit }: Props) {
  return (
    <div className="flex-1 rounded-2xl bg-surface border border-border/60 px-3 py-3 flex items-center gap-3">
      <div className="w-10 h-10 flex items-center justify-center shrink-0">
        <Flame
          size={26}
          className="text-primary"
          fill="#FF6A1A"
          style={{
            filter:
              "drop-shadow(0 0 4px rgba(255,230,170,0.65)) drop-shadow(0 0 10px rgba(255,140,40,0.55)) drop-shadow(0 0 16px rgba(255,90,0,0.35))",
          }}
        />
      </div>
      <div className="min-w-0 flex flex-col">
        <span
          style={{
            fontSize: 13,
            color: "#F5F5F5",
            fontWeight: 400,
            lineHeight: 1.2,
          }}
        >
          {label}
        </span>
        <span style={{ marginTop: 2, lineHeight: 1 }}>
          <span
            style={{
              fontFamily: "Oswald, Inter, sans-serif",
              fontSize: 28,
              fontWeight: 700,
              color: "#FF6A1A",
              letterSpacing: "-0.01em",
            }}
          >
            {value}
          </span>
          <span
            style={{
              marginLeft: 4,
              fontSize: 16,
              color: "#F5F5F5",
              fontWeight: 600,
            }}
          >
            {unit}
          </span>
        </span>
      </div>
    </div>
  );
}
