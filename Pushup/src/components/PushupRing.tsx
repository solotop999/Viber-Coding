type Props = { value: number; goal: number };

export default function PushupRing({ value, goal }: Props) {
  const pct = Math.min(1, value / goal);
  const size = 160;
  const stroke = 11;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const visibleFrac = 0.75; // 270° speedometer arc
  const arc = c * visibleFrac;
  const gap = c - arc;
  const fill = arc * pct;

  return (
    <div
      className="relative mx-4 rounded-3xl bg-surface border border-border/60 flex flex-col items-center overflow-hidden"
      style={{ padding: "12px 0 40px" }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_35%,rgba(255,106,26,0.22),transparent_65%)] pointer-events-none" />
      {/* container clips bottom gap of ring */}
      <div style={{ position: "relative", width: size, height: size - 42 }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{ transform: "rotate(135deg)", position: "absolute", top: 0, left: 0 }}
        >
          <defs>
            <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#FF8A3D" />
              <stop offset="100%" stopColor="#FF5A0A" />
            </linearGradient>
          </defs>
          <circle
            cx={size / 2} cy={size / 2} r={r}
            stroke="#2F2F35" strokeWidth={stroke}
            strokeLinecap="round" fill="none"
            strokeDasharray={`${arc} ${gap}`}
          />
          <circle
            cx={size / 2} cy={size / 2} r={r}
            stroke="url(#ringGrad)" strokeWidth={stroke}
            strokeLinecap="round" fill="none"
            strokeDasharray={`${fill} ${c - fill}`}
            style={{ filter: "drop-shadow(0 0 6px rgba(255,106,26,0.55))" }}
          />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 0 }}>
          <span style={{ fontSize: 10, letterSpacing: "0.22em", fontWeight: 600, color: "#8A8A90", fontFamily: "Inter, sans-serif" }}>
            PUSHUPS&nbsp;TODAY
          </span>
          <span style={{ fontSize: 60, lineHeight: 1, fontWeight: 700, color: "#F5F5F5", fontFamily: "Oswald, Inter, sans-serif", letterSpacing: "-0.01em", marginTop: 4 }}>
            {value}
          </span>
          <span style={{ fontSize: 10, letterSpacing: "0.32em", fontWeight: 600, color: "#8A8A90", fontFamily: "Inter, sans-serif", marginTop: 4 }}>
            TOTAL
          </span>
        </div>
      </div>
    </div>
  );
}
