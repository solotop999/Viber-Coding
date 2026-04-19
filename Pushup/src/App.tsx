import { useState } from "react";
import PhoneFrame from "./components/PhoneFrame";
import StatusBar from "./components/StatusBar";
import BottomTabBar from "./components/BottomTabBar";
import Dashboard from "./screens/Dashboard";
import Workouts from "./screens/Workouts";
import History from "./screens/History";
import Profile from "./screens/Profile";
import type { TabKey } from "./types";

export default function App() {
  const [tab, setTab] = useState<TabKey>("dashboard");

  return (
    <PhoneFrame>
      <div className="flex flex-col bg-bg relative" style={{ width: "100%", height: "100%" }}>
        <StatusBar />
        <div className="flex-1 overflow-y-auto no-scrollbar pb-24">
          {tab === "dashboard" && <Dashboard />}
          {tab === "workouts" && <Workouts />}
          {tab === "history" && <History />}
          {tab === "profile" && <Profile />}
        </div>
        <BottomTabBar active={tab} onChange={setTab} />
      </div>
    </PhoneFrame>
  );
}
