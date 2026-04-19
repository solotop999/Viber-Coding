import { HISTORY_LIMIT, PUSHUP_STORAGE_KEY, TODAY_GOAL } from "../model/constants";
import type {
  PushupHistoryItem,
  PushupSessionRecord,
  PushupTodayStats,
} from "../model/sessionTypes";

function safeWindow() {
  return typeof window !== "undefined" ? window : null;
}

function startOfLocalDay(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

function formatDayParts(date: Date) {
  return {
    monthLabel: date.toLocaleDateString(undefined, { month: "short" }),
    dayLabel: date.toLocaleDateString(undefined, { day: "2-digit" }),
  };
}

export function loadSessions() {
  const host = safeWindow();
  if (!host) {
    return [] as PushupSessionRecord[];
  }

  const raw = host.localStorage.getItem(PUSHUP_STORAGE_KEY);
  if (!raw) {
    return [] as PushupSessionRecord[];
  }

  try {
    const parsed = JSON.parse(raw) as PushupSessionRecord[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveCompletedSession(session: PushupSessionRecord) {
  if (session.repCount <= 0) {
    return;
  }

  const host = safeWindow();
  if (!host) {
    return;
  }

  const next = [session, ...loadSessions()].sort(
    (a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime(),
  );

  host.localStorage.setItem(PUSHUP_STORAGE_KEY, JSON.stringify(next));
}

export function getTodayStats(): PushupTodayStats {
  const todayStart = startOfLocalDay(new Date());
  const sessions = loadSessions();

  const todayPushups = sessions
    .filter((session) => startOfLocalDay(new Date(session.startedAt)) === todayStart)
    .reduce((total, session) => total + session.repCount, 0);

  return {
    pushups: todayPushups,
    goal: TODAY_GOAL,
    streak: getCurrentStreak(sessions),
  };
}

export function getCurrentStreak(sessions = loadSessions()) {
  const uniqueDays = new Set(
    sessions
      .filter((session) => session.repCount > 0)
      .map((session) => startOfLocalDay(new Date(session.startedAt))),
  );

  let streak = 0;
  let cursor = startOfLocalDay(new Date());

  while (uniqueDays.has(cursor)) {
    streak += 1;
    cursor -= 24 * 60 * 60 * 1000;
  }

  return streak;
}

export function getLast30DayCounts() {
  const sessions = loadSessions();
  const now = new Date();

  return Array.from({ length: 30 }, (_, index) => {
    const date = new Date(now.getFullYear(), now.getMonth(), now.getDate() - (29 - index));
    const target = startOfLocalDay(date);

    return sessions
      .filter((session) => startOfLocalDay(new Date(session.startedAt)) === target)
      .reduce((total, session) => total + session.repCount, 0);
  });
}

export function getRecentHistory(limit = HISTORY_LIMIT): PushupHistoryItem[] {
  return loadSessions()
    .slice(0, limit)
    .map((session) => {
      const startedAt = new Date(session.startedAt);
      const { dayLabel, monthLabel } = formatDayParts(startedAt);

      return {
        ...session,
        dayLabel,
        monthLabel,
        minutesLabel: Math.max(1, Math.round(session.durationSec / 60)).toString(),
      };
    });
}

export function getWeeklyHistorySummary() {
  const last7 = getLast30DayCounts().slice(-7);
  const total = last7.reduce((sum, value) => sum + value, 0);
  const average = last7.length ? Math.round(total / last7.length) : 0;

  return { total, average, chart: last7 };
}
