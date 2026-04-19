import { useEffect, useState } from "react";

export function useVisibilityPause() {
  const [isHidden, setIsHidden] = useState(document.visibilityState === "hidden");

  useEffect(() => {
    const onVisibilityChange = () => {
      setIsHidden(document.visibilityState === "hidden");
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, []);

  return isHidden;
}
