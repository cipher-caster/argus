/**
 * Zustand store for managing active indicators
 */

import { create } from "zustand";

export interface IndicatorConfig {
  id: string;
  type: string;
  displayName: string;
  indicatorType: "overlay" | "pane";
  params: Record<string, number>;
  color: string;
  visible: boolean;
}

export interface IndicatorDefinition {
  name: string;
  display_name: string;
  type: "overlay" | "pane";
  params: Array<{
    name: string;
    type: string;
    default: number;
    min: number;
    max: number;
  }>;
  description: string;
}

interface IndicatorStore {
  indicators: IndicatorConfig[];
  availableIndicators: IndicatorDefinition[];

  // Actions
  addIndicator: (type: string, params?: Record<string, number>) => void;
  removeIndicator: (id: string) => void;
  updateIndicator: (id: string, updates: Partial<IndicatorConfig>) => void;
  toggleVisibility: (id: string) => void;
  setAvailableIndicators: (indicators: IndicatorDefinition[]) => void;
  clearAll: () => void;
}

// Preset colors for indicators
const INDICATOR_COLORS = [
  "#6366f1", // Indigo
  "#f59e0b", // Amber
  "#10b981", // Emerald
  "#ef4444", // Red
  "#8b5cf6", // Violet
  "#06b6d4", // Cyan
  "#f97316", // Orange
  "#84cc16", // Lime
];

let colorIndex = 0;
const getNextColor = () => {
  const color = INDICATOR_COLORS[colorIndex % INDICATOR_COLORS.length];
  colorIndex++;
  return color;
};

export const useIndicatorStore = create<IndicatorStore>((set, get) => ({
  indicators: [],
  availableIndicators: [],

  addIndicator: (type: string, params?: Record<string, number>) => {
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
      color: getNextColor(),
      visible: true,
    };

    set((state) => ({ indicators: [...state.indicators, newIndicator] }));
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
