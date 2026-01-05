"use client";

import { IconButton } from "@/components/ui";
import { BarChart3, Circle, Hand, Minus, MousePointer2, Pencil, RectangleHorizontal, TrendingUp, Type } from "lucide-react";
import { useState } from "react";

type DrawingTool = "cursor" | "crosshair" | "trendline" | "horizontal" | "rectangle" | "circle" | "text" | "fib";

interface DrawingToolbarProps {
  onToolChange?: (tool: DrawingTool) => void;
}

const tools: { id: DrawingTool; icon: React.ReactNode; label: string }[] = [
  { id: "cursor", icon: <MousePointer2 size={18} />, label: "Cursor" },
  { id: "crosshair", icon: <Hand size={18} />, label: "Crosshair" },
  { id: "trendline", icon: <TrendingUp size={18} />, label: "Trend Line" },
  { id: "horizontal", icon: <Minus size={18} />, label: "Horizontal Line" },
  { id: "rectangle", icon: <RectangleHorizontal size={18} />, label: "Rectangle" },
  { id: "circle", icon: <Circle size={18} />, label: "Circle" },
  { id: "fib", icon: <BarChart3 size={18} />, label: "Fibonacci" },
  { id: "text", icon: <Type size={18} />, label: "Text" },
];

export function DrawingToolbar({ onToolChange }: DrawingToolbarProps) {
  const [activeTool, setActiveTool] = useState<DrawingTool>("cursor");

  const handleToolClick = (tool: DrawingTool) => {
    setActiveTool(tool);
    onToolChange?.(tool);
  };

  return (
    <div className="drawing-toolbar">
      {tools.map((tool) => (
        <IconButton key={tool.id} active={activeTool === tool.id} tooltip={tool.label} onClick={() => handleToolClick(tool.id)}>
          {tool.icon}
        </IconButton>
      ))}

      <div className="toolbar-divider" />

      <IconButton tooltip="Drawing Mode (Coming Soon)">
        <Pencil size={18} />
      </IconButton>

      <style jsx>{`
        .drawing-toolbar {
          display: flex;
          flex-direction: column;
          gap: 2px;
          padding: 8px 4px;
          background: var(--bg-secondary);
          border-right: 1px solid var(--border-color);
          height: 100%;
        }
        .toolbar-divider {
          height: 1px;
          margin: 8px 4px;
          background: var(--border-color);
        }
      `}</style>
    </div>
  );
}
