export type DeviceMode = "front-camera";

export type PushupSessionRecord = {
  id: string;
  startedAt: string;
  endedAt: string;
  durationSec: number;
  repCount: number;
  deviceMode: DeviceMode;
  averageFps?: number;
};

export type PushupHistoryItem = PushupSessionRecord & {
  dayLabel: string;
  monthLabel: string;
  minutesLabel: string;
};

export type PushupTodayStats = {
  pushups: number;
  goal: number;
  streak: number;
};
