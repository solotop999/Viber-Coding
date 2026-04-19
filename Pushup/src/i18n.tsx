import {
  createContext,
  useContext,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";

export type Language = "vi" | "en";

type Copy = {
  topBar: {
    languageLabel: string;
    vi: string;
    en: string;
  };
  tabs: Record<"dashboard" | "workouts" | "history" | "profile", string>;
  dashboard: {
    pushupsToday: string;
    total: string;
    caloriesBurned: string;
    currentStreak: string;
    days: string;
    progress30Day: string;
    barChart: string;
    startSession: string;
  };
  workouts: {
    title: string;
    categories: string[];
    start: string;
    minutes: string;
    levels: Record<"Easy" | "Medium" | "Hard", string>;
    titles: Record<string, string>;
    subtitles: Record<string, string>;
  };
  history: {
    title: string;
    thisWeek: string;
    totalReps: string;
    average: string;
    recentSessions: string;
    pushups: string;
  };
  profile: {
    title: string;
    joined: string;
    level: string;
    xpProgress: string;
    goal: string;
    streak: string;
    badges: string;
    achievements: string;
    achievementTitles: Record<string, string>;
    achievementDescs: Record<string, string>;
  };
};

const translations: Record<Language, Copy> = {
  vi: {
    topBar: {
      languageLabel: "Ngôn ngữ",
      vi: "VI",
      en: "EN",
    },
    tabs: {
      dashboard: "Tổng quan",
      workouts: "Bài tập",
      history: "Lịch sử",
      profile: "Hồ sơ",
    },
    dashboard: {
      pushupsToday: "HÔM NAY",
      total: "TỔNG",
      caloriesBurned: "Calo đã đốt",
      currentStreak: "Chuỗi hiện tại",
      days: "Ngày",
      progress30Day: "TIẾN ĐỘ 30 NGÀY",
      barChart: "Biểu đồ",
      startSession: "BẮT ĐẦU",
    },
    workouts: {
      title: "Bài tập",
      categories: ["Tất cả", "Dễ", "Vừa", "Khó"],
      start: "Bắt đầu",
      minutes: "phút",
      levels: {
        Easy: "Dễ",
        Medium: "Vừa",
        Hard: "Khó",
      },
      titles: {
        Beginner: "Người mới",
        Standard: "Tiêu chuẩn",
        Advanced: "Nâng cao",
        Diamond: "Kim cương",
        "Wide Grip": "Tay rộng",
        Explosive: "Bùng nổ",
      },
      subtitles: {
        beg: "3 hiệp · 10 lần",
        std: "4 hiệp · 15 lần",
        adv: "5 hiệp · 25 lần",
        dia: "4 hiệp · 12 lần",
        wide: "4 hiệp · 18 lần",
        exp: "5 hiệp · 10 lần",
      },
    },
    history: {
      title: "Lịch sử",
      thisWeek: "TUẦN NÀY",
      totalReps: "Tổng số lần",
      average: "Trung bình",
      recentSessions: "BUỔI GẦN ĐÂY",
      pushups: "lần hít đất",
    },
    profile: {
      title: "Hồ sơ",
      joined: "Tham gia",
      level: "CẤP",
      xpProgress: "Tiến trình XP",
      goal: "Mục tiêu",
      streak: "Chuỗi",
      badges: "Huy hiệu",
      achievements: "THÀNH TÍCH",
      achievementTitles: {
        "First 100": "100 đầu tiên",
        "Week Warrior": "Chiến binh tuần",
        Century: "Bách phát",
        "Iron Month": "Tháng thép",
      },
      achievementDescs: {
        "Reach 100 total pushups": "Đạt tổng 100 lần hít đất",
        "7-day streak": "Chuỗi 7 ngày",
        "100 in one session": "100 lần trong một buổi",
        "30-day streak": "Chuỗi 30 ngày",
      },
    },
  },
  en: {
    topBar: {
      languageLabel: "Language",
      vi: "VI",
      en: "EN",
    },
    tabs: {
      dashboard: "Dashboard",
      workouts: "Workouts",
      history: "History",
      profile: "Profile",
    },
    dashboard: {
      pushupsToday: "PUSHUPS TODAY",
      total: "TOTAL",
      caloriesBurned: "Calories Burned",
      currentStreak: "Current Streak",
      days: "Days",
      progress30Day: "30-DAY PROGRESS",
      barChart: "Bar Chart",
      startSession: "START SESSION",
    },
    workouts: {
      title: "Workouts",
      categories: ["All", "Easy", "Medium", "Hard"],
      start: "Start",
      minutes: "min",
      levels: {
        Easy: "Easy",
        Medium: "Medium",
        Hard: "Hard",
      },
      titles: {
        Beginner: "Beginner",
        Standard: "Standard",
        Advanced: "Advanced",
        Diamond: "Diamond",
        "Wide Grip": "Wide Grip",
        Explosive: "Explosive",
      },
      subtitles: {
        beg: "3 sets · 10 reps",
        std: "4 sets · 15 reps",
        adv: "5 sets · 25 reps",
        dia: "4 sets · 12 reps",
        wide: "4 sets · 18 reps",
        exp: "5 sets · 10 reps",
      },
    },
    history: {
      title: "History",
      thisWeek: "THIS WEEK",
      totalReps: "Total reps",
      average: "Average",
      recentSessions: "RECENT SESSIONS",
      pushups: "pushups",
    },
    profile: {
      title: "Profile",
      joined: "Joined",
      level: "LEVEL",
      xpProgress: "XP Progress",
      goal: "Goal",
      streak: "Streak",
      badges: "Badges",
      achievements: "ACHIEVEMENTS",
      achievementTitles: {
        "First 100": "First 100",
        "Week Warrior": "Week Warrior",
        Century: "Century",
        "Iron Month": "Iron Month",
      },
      achievementDescs: {
        "Reach 100 total pushups": "Reach 100 total pushups",
        "7-day streak": "7-day streak",
        "100 in one session": "100 in one session",
        "30-day streak": "30-day streak",
      },
    },
  },
};

type I18nContextValue = {
  lang: Language;
  setLang: Dispatch<SetStateAction<Language>>;
  copy: Copy;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Language>("vi");

  return (
    <I18nContext.Provider value={{ lang, setLang, copy: translations[lang] }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error("useI18n must be used within LanguageProvider");
  }

  return context;
}
