import CameraPreview from "./CameraPreview";
import CountdownOverlay from "./CountdownOverlay";
import DebugStrip from "./DebugStrip";
import ReadyCheckOverlay from "./ReadyCheckOverlay";
import SessionGuide from "./SessionGuide";
import SessionHud from "./SessionHud";
import { usePushupSession } from "../hooks/usePushupSession";

type SessionScreenProps = {
  onClose: () => void;
};

export default function SessionScreen({ onClose }: SessionScreenProps) {
  const { videoRef, frame, status, elapsedSec, error, poseLandmarks, finishSession } =
    usePushupSession();

  function handleClose() {
    finishSession();
    onClose();
  }

  return (
    <div className="relative h-full min-h-screen overflow-hidden bg-black text-white">
      <CameraPreview videoRef={videoRef} poseLandmarks={poseLandmarks} showSkeleton />
      <ReadyCheckOverlay ready={frame.debug.readyToCount} />
      <SessionHud elapsedSec={elapsedSec} repCount={frame.repCount} onClose={handleClose} />

      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-col items-center gap-3 px-5 pb-6">
        <DebugStrip frame={frame} visible={status !== "countdown"} />
        <SessionGuide
          message={error ?? frame.message}
          status={status}
          phase={frame.phase}
          calibrationProgress={frame.calibrationProgress}
          confidence={frame.confidence}
        />
      </div>

      <CountdownOverlay visible={status === "countdown"} message={frame.message} />
    </div>
  );
}
