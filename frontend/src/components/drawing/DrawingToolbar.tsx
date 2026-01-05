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

function DrawingToolbarComponent() {
  const activeTool = useDrawingStore((s) => s.activeTool);
  const setActiveTool = useDrawingStore((s) => s.setActiveTool);
  const clearAllDrawings = useDrawingStore((s) => s.clearAllDrawings);
  const selectedDrawingId = useDrawingStore((s) => s.selectedDrawingId);
  const deleteSelected = useDrawingStore((s) => s.deleteSelected);

  const handleToolClick = (type: DrawingType) => {
    setActiveTool(activeTool === type ? null : type);
  };

  return (
    <div className="drawing-toolbar">
      {/* Tool Buttons */}
      {TOOLS.map((tool) => (
        <button key={tool.type} className={`toolbar-btn ${activeTool === tool.type ? "active" : ""}`} onClick={() => handleToolClick(tool.type)} title={tool.label}>
          {tool.icon}
        </button>
      ))}

      <div className="toolbar-divider" />

      {/* Delete Selected */}
      <button className="toolbar-btn delete-btn" onClick={deleteSelected} disabled={!selectedDrawingId} title="Delete Selected (Del)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
          <line x1="10" y1="11" x2="10" y2="17" />
          <line x1="14" y1="11" x2="14" y2="17" />
        </svg>
      </button>

      <style jsx>{`
        .drawing-toolbar {
          display: flex;
          flex-direction: column;
          gap: 4px;
          padding: 8px;
          background: #12121a;
          border-radius: 10px;
          border: 1px solid #1a1a2e;
        }

        .toolbar-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          background: transparent;
          border: none;
          border-radius: 6px;
          color: #606070;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .toolbar-btn:hover:not(:disabled) {
          background: #1a1a2e;
          color: #a0a0b0;
        }

        .toolbar-btn.active {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%);
          color: #a5b4fc;
        }

        .toolbar-btn:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .toolbar-btn :global(svg) {
          width: 18px;
          height: 18px;
        }

        .toolbar-divider {
          height: 1px;
          background: #1a1a2e;
          margin: 4px 0;
        }

        .delete-btn:hover:not(:disabled) {
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
        }
      `}</style>
    </div>
  );
}

export const DrawingToolbar = memo(DrawingToolbarComponent);
