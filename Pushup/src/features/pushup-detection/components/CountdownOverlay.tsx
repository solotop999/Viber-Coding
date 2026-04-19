type CountdownOverlayProps = {
  visible: boolean;
  message: string;
};

export default function CountdownOverlay({ visible, message }: CountdownOverlayProps) {
  if (!visible) {
    return null;
  }

  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="rounded-[28px] border border-white/10 bg-black/45 px-8 py-6 text-center backdrop-blur-md">
        <div className="text-[12px] font-semibold uppercase tracking-[0.28em] text-white/60">
          Prepare
        </div>
        <div className="mt-2 text-[28px] font-black text-white">{message}</div>
      </div>
    </div>
  );
}
