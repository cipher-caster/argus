/**
 * Zustand store for managing chart drawings
 */

import { create } from "zustand";

export interface Point {
  time: number; // Unix timestamp in seconds
  price: number;
}

export interface DrawingStyle {
  color: string;
  lineWidth: number;
  lineStyle: "solid" | "dashed" | "dotted";
  fillColor?: string;
  fillOpacity?: number;
  fontSize?: number;
}

export type DrawingType = "trendline" | "hline" | "vline" | "ray" | "rectangle" | "fib" | "brush" | "text";

export interface FibLevel {
  level: number; // 0.0, 0.236, 0.382, etc.
  enabled: boolean;
  color?: string; // Override default color
}

export interface Drawing {
  id: string;
  type: DrawingType;
  points: Point[];
  style: DrawingStyle;
  symbol: string;
  text?: string; // For text tool
  fibLevels?: FibLevel[]; // For fib tool
  brushPath?: Point[]; // For brush tool
}

// Default Fib levels
export const DEFAULT_FIB_LEVELS: FibLevel[] = [
  { level: 0, enabled: true },
  { level: 0.236, enabled: true },
  { level: 0.382, enabled: true },
  { level: 0.5, enabled: true },
  { level: 0.618, enabled: true },
  { level: 0.786, enabled: true },
  { level: 1, enabled: true },
  { level: 1.272, enabled: false },
  { level: 1.618, enabled: false },
];

// Default drawing style
export const DEFAULT_STYLE: DrawingStyle = {
  color: "#6366f1",
  lineWidth: 2,
  lineStyle: "solid",
  fillColor: "#6366f1",
  fillOpacity: 0.1,
  fontSize: 14,
};

interface DrawingStore {
  drawings: Drawing[];
  activeTool: DrawingType | null;
  selectedDrawingId: string | null;
  isDrawing: boolean;
  currentPoints: Point[];
  defaultStyle: DrawingStyle;
  defaultFibLevels: FibLevel[];

  // Tool actions
  setActiveTool: (tool: DrawingType | null) => void;
  startDrawing: (point: Point) => void;
  updateDrawing: (point: Point) => void;
  finishDrawing: (symbol: string, text?: string) => void;
  cancelDrawing: () => void;

  // Drawing management
  selectDrawing: (id: string | null) => void;
  deleteDrawing: (id: string) => void;
  deleteSelected: () => void;
  updateDrawingStyle: (id: string, style: Partial<DrawingStyle>) => void;
  updateDrawingPoints: (id: string, points: Point[]) => void;
  clearAllDrawings: (symbol: string) => void;

  // Style settings
  setDefaultStyle: (style: Partial<DrawingStyle>) => void;
  setDefaultFibLevels: (levels: FibLevel[]) => void;

  // Persistence
  saveToLocalStorage: () => void;
  loadFromLocalStorage: (symbol: string) => void;
}

export const useDrawingStore = create<DrawingStore>((set, get) => ({
  drawings: [],
  activeTool: null,
  selectedDrawingId: null,
  isDrawing: false,
  currentPoints: [],
  defaultStyle: DEFAULT_STYLE,
  defaultFibLevels: DEFAULT_FIB_LEVELS,

  setActiveTool: (tool) => {
    set({ activeTool: tool, selectedDrawingId: null, isDrawing: false, currentPoints: [] });
  },

  startDrawing: (point) => {
    set({ isDrawing: true, currentPoints: [point] });
  },

  updateDrawing: (point) => {
    const { currentPoints, activeTool } = get();
    if (activeTool === "brush") {
      // Brush accumulates all points
      set({ currentPoints: [...currentPoints, point] });
    } else {
      // Other tools just update the second point
      set({ currentPoints: [currentPoints[0], point] });
    }
  },

  finishDrawing: (symbol, text) => {
    const { activeTool, currentPoints, defaultStyle, defaultFibLevels } = get();
    if (!activeTool || currentPoints.length === 0) return;

    // Single-point tools (hline, vline, text) need only 1 point
    const minPoints = ["hline", "vline", "text"].includes(activeTool) ? 1 : 2;
    if (currentPoints.length < minPoints) {
      set({ isDrawing: false, currentPoints: [] });
      return;
    }

    const newDrawing: Drawing = {
      id: `${activeTool}-${Date.now()}`,
      type: activeTool,
      points: currentPoints,
      style: { ...defaultStyle },
      symbol,
      text: text,
      fibLevels: activeTool === "fib" ? [...defaultFibLevels] : undefined,
      brushPath: activeTool === "brush" ? [...currentPoints] : undefined,
    };

    set((state) => ({
      drawings: [...state.drawings, newDrawing],
      isDrawing: false,
      currentPoints: [],
      activeTool: null, // Deselect tool after drawing
    }));

    // Auto-save
    setTimeout(() => get().saveToLocalStorage(), 0);
  },

  cancelDrawing: () => {
    set({ isDrawing: false, currentPoints: [], activeTool: null });
  },

  selectDrawing: (id) => {
    set({ selectedDrawingId: id, activeTool: null });
  },

  deleteDrawing: (id) => {
    set((state) => ({
      drawings: state.drawings.filter((d) => d.id !== id),
      selectedDrawingId: state.selectedDrawingId === id ? null : state.selectedDrawingId,
    }));
    setTimeout(() => get().saveToLocalStorage(), 0);
  },

  deleteSelected: () => {
    const { selectedDrawingId } = get();
    if (selectedDrawingId) {
      get().deleteDrawing(selectedDrawingId);
    }
  },

  updateDrawingStyle: (id, style) => {
    set((state) => ({
      drawings: state.drawings.map((d) => (d.id === id ? { ...d, style: { ...d.style, ...style } } : d)),
    }));
    setTimeout(() => get().saveToLocalStorage(), 0);
  },

  updateDrawingPoints: (id, points) => {
    set((state) => ({
      drawings: state.drawings.map((d) => (d.id === id ? { ...d, points } : d)),
    }));
    setTimeout(() => get().saveToLocalStorage(), 0);
  },

  clearAllDrawings: (symbol) => {
    set((state) => ({
      drawings: state.drawings.filter((d) => d.symbol !== symbol),
      selectedDrawingId: null,
    }));
    setTimeout(() => get().saveToLocalStorage(), 0);
  },

  setDefaultStyle: (style) => {
    set((state) => ({
      defaultStyle: { ...state.defaultStyle, ...style },
    }));
  },

  setDefaultFibLevels: (levels) => {
    set({ defaultFibLevels: levels });
  },

  saveToLocalStorage: () => {
    const { drawings, defaultStyle, defaultFibLevels } = get();
    try {
      localStorage.setItem("magus-drawings", JSON.stringify(drawings));
      localStorage.setItem("magus-drawing-style", JSON.stringify(defaultStyle));
      localStorage.setItem("magus-fib-levels", JSON.stringify(defaultFibLevels));
    } catch (e) {
      if (process.env.NODE_ENV === "development") console.error("Failed to save drawings:", e);
    }
  },

  loadFromLocalStorage: (symbol) => {
    try {
      const stored = localStorage.getItem("magus-drawings");
      const storedStyle = localStorage.getItem("magus-drawing-style");
      const storedFib = localStorage.getItem("magus-fib-levels");

      if (stored) {
        const allDrawings: Drawing[] = JSON.parse(stored);
        set({ drawings: allDrawings });
      }
      if (storedStyle) {
        set({ defaultStyle: JSON.parse(storedStyle) });
      }
      if (storedFib) {
        set({ defaultFibLevels: JSON.parse(storedFib) });
      }
    } catch (e) {
      if (process.env.NODE_ENV === "development") console.error("Failed to load drawings:", e);
    }
  },
}));
