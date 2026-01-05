/**
 * Theme Store
 * Zustand store for managing light/dark theme
 */

import { create } from "zustand";

export type Theme = "light" | "dark";

interface ThemeStore {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

export const useThemeStore = create<ThemeStore>((set) => ({
  theme: "light", // Default to light mode

  toggleTheme: () => {
    set((state) => {
      const newTheme = state.theme === "light" ? "dark" : "light";
      // Update document class for CSS
      if (typeof document !== "undefined") {
        document.documentElement.setAttribute("data-theme", newTheme);
      }
      return { theme: newTheme };
    });
  },

  setTheme: (theme: Theme) => {
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", theme);
    }
    set({ theme });
  },
}));

// Theme color definitions
export const themes = {
  light: {
    background: "#ffffff",
    backgroundSecondary: "#f5f5f7",
    backgroundTertiary: "#e8e8eb",
    text: "#1a1a1a",
    textSecondary: "#606070",
    border: "#d1d1d6",
    accent: "#6366f1",
    positive: "#10b981",
    negative: "#ef4444",
    warning: "#f59e0b",
    info: "#3b82f6",
    chart: {
      background: "#ffffff",
      gridLines: "#e8e8eb",
      text: "#606070",
      crosshair: "#9ca3af",
    },
  },
  dark: {
    background: "#0a0a0f",
    backgroundSecondary: "#12121a",
    backgroundTertiary: "#1a1a2e",
    text: "#ffffff",
    textSecondary: "#a0a0b0",
    border: "#2a2a4a",
    accent: "#6366f1",
    positive: "#00dc82",
    negative: "#ff4757",
    warning: "#fdba74",
    info: "#60a5fa",
    chart: {
      background: "#0a0a0f",
      gridLines: "#1a1a2e",
      text: "#a0a0b0",
      crosshair: "#4a4a6a",
    },
  },
};
