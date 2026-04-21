import { useEffect, useRef, useState } from "react";
import { CircleCheckBig } from "lucide-react";

type ReadyCheckOverlayProps = {
  ready: boolean;
};

export default function ReadyCheckOverlay({ ready }: ReadyCheckOverlayProps) {
  const previousReadyRef = useRef(false);
  const [visible, setVisible] = useState(false);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    if (ready && !previousReadyRef.current) {
      setVisible(true);
      setFading(false);

      const fadeTimer = window.setTimeout(() => setFading(true), 700);
      const hideTimer = window.setTimeout(() => {
        setVisible(false);
        setFading(false);
      }, 1300);

      previousReadyRef.current = ready;

      return () => {
        window.clearTimeout(fadeTimer);
        window.clearTimeout(hideTimer);
      };
    }

    previousReadyRef.current = ready;
  }, [ready]);

  if (!visible) {
    return null;
  }

  return (
    <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center">
      <div
        className={`flex flex-col items-center gap-5 text-[#73FFA8] transition-opacity duration-500 ${
          fading ? "opacity-0" : "opacity-100"
        }`}
      >
        <CircleCheckBig
          size={128}
          strokeWidth={2.6}
          className="drop-shadow-[0_10px_28px_rgba(115,255,168,0.45)]"
        />
        <div className="text-center">
          <div className="text-[16px] font-semibold uppercase tracking-[0.28em] text-white/75">
            Ready
          </div>
          <div className="mt-2 text-[32px] font-black tracking-[-0.04em] text-white">
            San Sang
          </div>
        </div>
      </div>
    </div>
  );
}
