export const user = {
  name: "Alex Carter",
  handle: "@alex.c",
  joined: "Mar 2025",
  level: 7,
  xp: 2840,
  xpToNext: 3500,
};

export const todayStats = {
  pushups: 75,
  goal: 100,
  calories: 435,
  streak: 12,
};

export const last30Days: number[] = [
  22, 30, 18, 45, 12, 38, 28, 50, 33, 40,
  25, 55, 42, 60, 48, 20, 35, 52, 44, 58,
  30, 46, 62, 54, 70, 40, 48, 66, 75, 55,
];

export const workouts = [
  { id: "beg", title: "Beginner", subtitle: "3 sets · 10 reps", minutes: 8, level: "Easy", color: "#4ADE80" },
  { id: "std", title: "Standard", subtitle: "4 sets · 15 reps", minutes: 12, level: "Medium", color: "#FF6A1A" },
  { id: "adv", title: "Advanced", subtitle: "5 sets · 25 reps", minutes: 18, level: "Hard", color: "#F43F5E" },
  { id: "dia", title: "Diamond", subtitle: "4 sets · 12 reps", minutes: 14, level: "Hard", color: "#A855F7" },
  { id: "wide", title: "Wide Grip", subtitle: "4 sets · 18 reps", minutes: 12, level: "Medium", color: "#38BDF8" },
  { id: "exp", title: "Explosive", subtitle: "5 sets · 10 reps", minutes: 16, level: "Hard", color: "#FACC15" },
];

export const history = [
  { date: "Apr 19", reps: 75, kcal: 435, minutes: 14 },
  { date: "Apr 18", reps: 68, kcal: 395, minutes: 12 },
  { date: "Apr 17", reps: 72, kcal: 418, minutes: 13 },
  { date: "Apr 16", reps: 60, kcal: 348, minutes: 11 },
  { date: "Apr 15", reps: 80, kcal: 464, minutes: 15 },
  { date: "Apr 14", reps: 55, kcal: 319, minutes: 10 },
  { date: "Apr 13", reps: 70, kcal: 406, minutes: 13 },
];

export const achievements = [
  { id: "a1", title: "First 100", desc: "Reach 100 total pushups", unlocked: true },
  { id: "a2", title: "Week Warrior", desc: "7-day streak", unlocked: true },
  { id: "a3", title: "Century", desc: "100 in one session", unlocked: false },
  { id: "a4", title: "Iron Month", desc: "30-day streak", unlocked: false },
];
