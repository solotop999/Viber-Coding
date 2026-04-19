type Props = { value: number; goal: number };

export default function PushupRing({ value, goal }: Props) {
  const pct = Math.min(1, value / goal);

  // Geometry
  const size = 160;             // logical SVG square
  const stroke = 11;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const visibleFrac = 0.75;     // 270° speedometer arc
  const arc = c * visibleFrac;
  const fill = arc * pct;

  // Bottom of arc after 135° rotation sits at ~85% of size.
  // Crop viewBox to remove unused empty space below.
  const visibleH = Math.round(size * 0.86);

  return (
    <div className="relative mx-4 rounded-3xl bg-surface border border-border/60 overflow-hidden py-4">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_35%,rgba(255,106,26,0.10),transparent_60%)] pointer-events-none" />

      <div
        className="relative mx-auto"
        style={{ width: size, height: visibleH }}
      >
        <svg
          width={size}
          height={visibleH}
          viewBox={`0 0 ${size} ${visibleH}`}
          className="absolute inset-0"
        >
          <defs>
            <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#FF8A3D" />
              <stop offset="100%" stopColor="#FF5A0A" />
            </linearGradient>
          </defs>
          {/* rotate inside SVG so viewBox clipping happens after rotation */}
          <g transform={`rotate(135 ${size / 2} ${size / 2})`}>
            <circle
              cx={size / 2} cy={size / 2} r={r}
              stroke="#2F2F35" strokeWidth={stroke}
              strokeLinecap="round" fill="none"
              strokeDasharray={`${arc} ${c - arc}`}
            />
            <circle
              cx={size / 2} cy={size / 2} r={r}
              stroke="url(#ringGrad)" strokeWidth={stroke}
              strokeLinecap="round" fill="none"
              strokeDasharray={`${fill} ${c - fill}`}
              style={{ filter: "drop-shadow(0 0 2px rgba(255,106,26,0.35))" }}
            />
          </g>
        </svg>

        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center">
          <span className="text-[10px] tracking-[0.22em] font-semibold text-text">
            PUSHUPS&nbsp;TODAY
          </span>
          <span
            className="font-bold text-text mt-1"
            style={{ fontSize: 60, lineHeight: 1, fontFamily: "Oswald, Inter, sans-serif", letterSpacing: "-0.01em" }}
          >
            {value}
          </span>
          <span className="text-[10px] tracking-[0.32em] font-semibold text-text mt-1">
            TOTAL
          </span>
        </div>
      </div>
    </div>
  );
}
