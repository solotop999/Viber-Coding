import { useEffect, useState } from "react";
import PhoneFrame from "./components/PhoneFrame";
import StatusBar from "./components/StatusBar";
import BottomTabBar from "./components/BottomTabBar";
import Dashboard from "./screens/Dashboard";
import Workouts from "./screens/Workouts";
import History from "./screens/History";
import Profile from "./screens/Profile";
import { SessionScreen, VideoDebugScreen } from "./features/pushup-detection";
import type { AppMode, TabKey } from "./types";
import backgroundImage from "../background.png";

export default function App() {
  const [tab, setTab] = useState<TabKey>("dashboard");
  const [mode, setMode] = useState<AppMode>(() => {
    const { pathname } = window.location;

    if (pathname === "/debug") {
      return "video-debug";
    }

    if (pathname === "/session") {
      return "session";
    }

    return "shell";
  });

  useEffect(() => {
    const url = new URL(window.location.href);

    if (mode === "video-debug") {
      url.pathname = "/debug";
      url.search = "";
    } else if (mode === "session") {
      url.pathname = "/session";
      url.search = "";
    } else {
      url.pathname = "/";
      url.search = "";
    }

    window.history.replaceState({}, "", url);
  }, [mode]);

  if (mode === "session") {
    return (
      <PhoneFrame>
        <SessionScreen onClose={() => setMode("shell")} />
      </PhoneFrame>
    );
  }

  if (mode === "video-debug") {
    return (
      <PhoneFrame>
        <VideoDebugScreen onClose={() => setMode("shell")} />
      </PhoneFrame>
    );
  }

  return (
    <PhoneFrame>
      <div
        className="flex flex-col bg-bg relative app-screen-background"
        style={{
          width: "100%",
          height: "100%",
          backgroundImage: `linear-gradient(180deg, rgba(14, 14, 16, 0.22) 0%, rgba(14, 14, 16, 0.72) 100%), url(${backgroundImage})`,
        }}
      >
        <StatusBar />
        <div className="flex-1 overflow-y-auto no-scrollbar pb-24">
          {tab === "dashboard" && (
            <Dashboard
              onStartSession={() => setMode("session")}
              onOpenVideoDebug={() => setMode("video-debug")}
            />
          )}
          {tab === "workouts" && <Workouts />}
          {tab === "history" && <History />}
          {tab === "profile" && <Profile />}
        </div>
        <BottomTabBar active={tab} onChange={setTab} />
      </div>
    </PhoneFrame>
  );
}
