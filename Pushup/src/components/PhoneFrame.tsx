import { useEffect, useRef, useState, type ReactNode } from "react";

type Props = { children: ReactNode };

// Design base size (iPhone 17 Pro Max ratio 78:163.4)
const BASE_W = 393;
const BASE_H = Math.round((393 * 163.4) / 78); // 823

export default function PhoneFrame({ children }: Props) {
  const screenRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const el = screenRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      const w = el.clientWidth;
      setScale(w / BASE_W);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div className="w-full h-full flex items-center justify-center p-4">
      <div
        className="relative bg-black rounded-[52px] shadow-[0_30px_80px_-20px_rgba(255,106,26,0.25),0_0_0_2px_#1a1a1f,0_0_0_10px_#0a0a0c]"
        style={{
          aspectRatio: `${BASE_W} / ${BASE_H}`,
          height: `min(96vh, calc(96vw * ${BASE_H} / ${BASE_W}))`,
        }}
      >
        {/* Side buttons */}
        <div className="absolute -left-[10px] top-[22%] w-[3px] h-[32px] bg-[#1a1a1f] rounded-l-sm" />
        <div className="absolute -left-[10px] top-[30%] w-[3px] h-[56px] bg-[#1a1a1f] rounded-l-sm" />
        <div className="absolute -left-[10px] top-[38%] w-[3px] h-[56px] bg-[#1a1a1f] rounded-l-sm" />
        <div className="absolute -right-[10px] top-[30%] w-[3px] h-[80px] bg-[#1a1a1f] rounded-r-sm" />

        {/* Screen */}
        <div
          ref={screenRef}
          className="absolute inset-[6px] rounded-[46px] overflow-hidden bg-bg"
        >
          {/* scaled design surface */}
          <div
            style={{
              width: BASE_W,
              height: BASE_H,
              transform: `scale(${scale})`,
              transformOrigin: "top left",
              position: "relative",
            }}
          >
            {/* Dynamic island */}
            <div
              style={{
                position: "absolute",
                top: 10,
                left: "50%",
                transform: "translateX(-50%)",
                zIndex: 50,
                width: "35%",
                height: 28,
                background: "#000",
                borderRadius: 9999,
              }}
            />
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
