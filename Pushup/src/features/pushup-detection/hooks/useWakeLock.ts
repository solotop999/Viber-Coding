import { useEffect, useRef } from "react";

export function useWakeLock(enabled: boolean) {
  const sentinelRef = useRef<WakeLockSentinel | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function acquire() {
      if (!enabled || !navigator.wakeLock) {
        return;
      }

      try {
        sentinelRef.current = await navigator.wakeLock.request("screen");
        if (cancelled) {
          await sentinelRef.current?.release();
          sentinelRef.current = null;
        }
      } catch {
        sentinelRef.current = null;
      }
    }

    void acquire();

    return () => {
      cancelled = true;
      void sentinelRef.current?.release();
      sentinelRef.current = null;
    };
  }, [enabled]);
}
