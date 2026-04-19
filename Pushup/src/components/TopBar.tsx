import { Flame } from "lucide-react";
import { useI18n } from "../i18n";

export default function TopBar() {
  const { lang, setLang, copy } = useI18n();

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
      <button
        onClick={() => setLang((current) => (current === "vi" ? "en" : "vi"))}
        className="w-9 h-9 rounded-full bg-surface border border-border flex items-center justify-center"
        aria-label={copy.topBar.languageLabel}
        title={copy.topBar.languageLabel}
      >
        <span className="text-[11px] font-bold text-white leading-none">
          {lang === "vi" ? copy.topBar.vi : copy.topBar.en}
        </span>
      </button>
    </div>
  );
}
