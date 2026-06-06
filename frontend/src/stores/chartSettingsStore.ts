import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface ChartColorSettings {
  upColor: string | null;
  downColor: string | null;
  borderUpColor: string | null;
  borderDownColor: string | null;
  wickUpColor: string | null;
  wickDownColor: string | null;
}

interface ChartSettingsStore {
  colors: ChartColorSettings;
  setColors: (colors: Partial<ChartColorSettings>) => void;
  resetColors: () => void;
}

const DEFAULT_COLORS: ChartColorSettings = {
  upColor: null, // Use theme default
  downColor: null,
  borderUpColor: null,
  borderDownColor: null,
  wickUpColor: null,
  wickDownColor: null,
};

export const useChartSettingsStore = create<ChartSettingsStore>()(
  persist(
    (set) => ({
      colors: DEFAULT_COLORS,
      setColors: (updates) =>
        set((state) => ({
          colors: { ...state.colors, ...updates },
        })),
      resetColors: () => set({ colors: DEFAULT_COLORS }),
    }),
    {
      name: "chart-settings-storage",
    }
  )
);
