export default function HeroImage() {
  return (
    <div className="mx-4 mt-3 rounded-2xl overflow-hidden h-[130px] relative bg-gradient-to-br from-[#2a1810] via-[#1a1010] to-[#0a0505]">
      {/* Stylized pushup silhouette using SVG */}
      <svg
        viewBox="0 0 300 130"
        className="absolute inset-0 w-full h-full"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <radialGradient id="spot" cx="50%" cy="30%" r="60%">
            <stop offset="0%" stopColor="#FF6A1A" stopOpacity="0.22" />
            <stop offset="60%" stopColor="#FF6A1A" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="300" height="130" fill="url(#spot)" />
        {/* Floor */}
        <rect x="0" y="100" width="300" height="30" fill="#0a0505" />
        {/* Body silhouette */}
        <g fill="#1a0f0a" stroke="#3a1f12" strokeWidth="0.5">
          {/* torso */}
          <path d="M60 95 Q80 70 130 68 Q180 66 220 82 Q245 92 250 100 L60 100 Z" />
          {/* head */}
          <ellipse cx="235" cy="78" rx="18" ry="14" />
          {/* arm */}
          <path d="M200 85 Q205 100 200 100 L185 100 Q188 92 195 85 Z" />
          <path d="M120 85 Q125 100 120 100 L105 100 Q108 92 115 85 Z" />
        </g>
        {/* Highlight on back */}
        <path
          d="M80 82 Q140 72 210 78"
          stroke="#FF6A1A"
          strokeWidth="1.5"
          fill="none"
          opacity="0.4"
        />
      </svg>
      <div className="absolute inset-0 bg-gradient-to-t from-bg/90 via-transparent to-transparent" />
    </div>
  );
}
