import { create } from "zustand";
import { IndicatorDefinition } from "@/lib/indicatorApi";

export type { IndicatorDefinition };

export interface IndicatorConfig {
  id: string;
  type: string;
  displayName: string;
  indicatorType: "overlay" | "pane";
  params: Record<string, number>;
  color: string;
  visible: boolean;
}

interface IndicatorStore {
  indicators: IndicatorConfig[];
  availableIndicators: IndicatorDefinition[];
  colorIndex: number;

  // Actions
  addIndicator: (type: string, params?: Record<string, number>, color?: string) => void;
  removeIndicator: (id: string) => void;
  updateIndicator: (id: string, updates: Partial<IndicatorConfig>) => void;
  toggleVisibility: (id: string) => void;
  setAvailableIndicators: (indicators: IndicatorDefinition[]) => void;
  clearAll: () => void;
}

// Preset colors for indicators
export const INDICATOR_COLORS = [
  "#6366f1", // Indigo
  "#f59e0b", // Amber
  "#10b981", // Emerald
  "#ef4444", // Red
  "#8b5cf6", // Violet
  "#06b6d4", // Cyan
  "#f97316", // Orange
  "#84cc16", // Lime
];

export const getNextColor = (index: number) => {
  return INDICATOR_COLORS[index % INDICATOR_COLORS.length];
};

export const useIndicatorStore = create<IndicatorStore>((set, get) => ({
  indicators: [],
  availableIndicators: [],
  colorIndex: 0,

  addIndicator: (type: string, params?: Record<string, number>, color?: string) => {
    const available = get().availableIndicators.find((i) => i.name === type);
    if (!available) return;

    // Build default params from definition
    const defaultParams: Record<string, number> = {};
    available.params.forEach((p) => {
      defaultParams[p.name] = params?.[p.name] ?? p.default;
    });

    const newIndicator: IndicatorConfig = {
      id: `${type}-${Date.now()}`,
      type,
      displayName: `${available.display_name}(${Object.values(defaultParams).join(",")})`,
      indicatorType: available.type,
      params: defaultParams,
      color: color || getNextColor(get().colorIndex),
      visible: true,
    };

    set((state) => ({ indicators: [...state.indicators, newIndicator], colorIndex: state.colorIndex + 1 }));
  },

  removeIndicator: (id: string) => {
    set((state) => ({
      indicators: state.indicators.filter((i) => i.id !== id),
    }));
  },

  updateIndicator: (id: string, updates: Partial<IndicatorConfig>) => {
    set((state) => ({
      indicators: state.indicators.map((i) => (i.id === id ? { ...i, ...updates } : i)),
    }));
  },

  toggleVisibility: (id: string) => {
    set((state) => ({
      indicators: state.indicators.map((i) => (i.id === id ? { ...i, visible: !i.visible } : i)),
    }));
  },

  setAvailableIndicators: (indicators: IndicatorDefinition[]) => {
    set({ availableIndicators: indicators });
  },

  clearAll: () => {
    set({ indicators: [] });
  },
}));
