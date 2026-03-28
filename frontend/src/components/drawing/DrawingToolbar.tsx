"use client";

/**
 * Drawing Toolbar Component
 * Vertical toolbar for selecting drawing tools
 */

import { DrawingType, useDrawingStore } from "@/stores/drawingStore";
import { memo } from "react";

interface ToolDefinition {
  type: DrawingType;
  icon: React.ReactNode;
  label: string;
  category: string;
}

const TOOLS: ToolDefinition[] = [
  {
    type: "trendline",
    category: "lines",
    label: "Trend Line",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <line x1="4" y1="20" x2="20" y2="4" />
      </svg>
    ),
  },
  {
    type: "hline",
    category: "lines",
    label: "Horizontal Line",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <line x1="4" y1="12" x2="20" y2="12" />
      </svg>
    ),
  },
  {
    type: "vline",
    category: "lines",
    label: "Vertical Line",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <line x1="12" y1="4" x2="12" y2="20" />
      </svg>
    ),
  },
  {
    type: "ray",
    category: "lines",
    label: "Ray",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <line x1="4" y1="16" x2="20" y2="8" />
        <circle cx="20" cy="8" r="2" fill="currentColor" />
      </svg>
    ),
  },
  {
    type: "rectangle",
    category: "shapes",
    label: "Rectangle",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <rect x="4" y="6" width="16" height="12" rx="1" />
      </svg>
    ),
  },
  {
    type: "fib",
    category: "fib",
    label: "Fib Retracement",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
        <line x1="4" y1="4" x2="20" y2="4" />
        <line x1="4" y1="8" x2="20" y2="8" opacity="0.7" />
        <line x1="4" y1="12" x2="20" y2="12" opacity="0.5" />
        <line x1="4" y1="16" x2="20" y2="16" opacity="0.3" />
        <line x1="4" y1="20" x2="20" y2="20" />
      </svg>
    ),
  },
  {
    type: "brush",
    category: "freehand",
    label: "Brush",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <path d="M4 20c2-2 4-6 8-8s6-6 8-8" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    type: "text",
    category: "annotation",
    label: "Text",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <text x="6" y="18" fontSize="16" fontWeight="bold" fill="currentColor" stroke="none">
          T
        </text>
      </svg>
    ),
  },
];

import { cn } from "@/lib/utils";

interface DrawingToolbarProps {
  symbol: string;
}

function DrawingToolbarComponent({ symbol }: DrawingToolbarProps) {
  const activeTool = useDrawingStore((s) => s.activeTool);
  const setActiveTool = useDrawingStore((s) => s.setActiveTool);
  const selectedDrawingId = useDrawingStore((s) => s.selectedDrawingId);
  const drawings = useDrawingStore((s) => s.drawings);
  const deleteSelected = useDrawingStore((s) => s.deleteSelected);
  const clearAllDrawings = useDrawingStore((s) => s.clearAllDrawings);

  const handleToolClick = (type: DrawingType) => {
    setActiveTool(activeTool === type ? null : type);
  };

  const symbolDrawingCount = drawings.filter((d) => d.symbol === symbol).length;

  return (
    <div className="flex flex-col gap-1 p-2 bg-secondary border border-border rounded-xl shadow-sm h-full overflow-y-auto w-12 items-center">
      {/* Tool Buttons */}
      {TOOLS.map((tool) => (
        <button
          key={tool.type}
          className={cn(
            "flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200",
            "text-muted-foreground hover:bg-muted hover:text-foreground active:scale-95 group",
            activeTool === tool.type ? "bg-primary/20 text-primary shadow-inner" : "bg-transparent"
          )}
          onClick={() => handleToolClick(tool.type)}
          title={tool.label}
        >
          <span className={cn("w-5 h-5", activeTool === tool.type ? "text-primary" : "text-muted-foreground group-hover:text-foreground")}>{tool.icon}</span>
        </button>
      ))}

      <div className="w-full h-px bg-border my-1" />

      {/* Delete Selected */}
      <button
        className={cn(
          "flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200",
          "text-muted-foreground hover:bg-destructive/10 hover:text-destructive active:scale-95 disabled:opacity-20 disabled:cursor-not-allowed",
          "bg-transparent"
        )}
        onClick={deleteSelected}
        disabled={!selectedDrawingId}
        title="Delete Selected (Del)"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5">
          <path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
          <line x1="10" y1="11" x2="10" y2="17" />
          <line x1="14" y1="11" x2="14" y2="17" />
        </svg>
      </button>

      {/* Clear All */}
      <button
        className={cn(
          "flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200",
          "text-muted-foreground hover:bg-destructive/10 hover:text-destructive active:scale-95 disabled:opacity-20 disabled:cursor-not-allowed",
          "bg-transparent"
        )}
        onClick={() => clearAllDrawings(symbol)}
        disabled={symbolDrawingCount === 0}
        title="Clear All Drawings"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="w-5 h-5">
          <path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" strokeLinecap="round" />
          <line x1="4" y1="4" x2="20" y2="20" strokeWidth={2.5} />
        </svg>
      </button>
    </div>
  );
}

export const DrawingToolbar = memo(DrawingToolbarComponent);
