"use client";

import { IconButton } from "@/components/ui";
import { MousePointer2, RefreshCw } from "lucide-react";

interface DrawingToolbarProps {
  onScrollToLatest?: () => void;
}

export function DrawingToolbar({ onScrollToLatest }: DrawingToolbarProps) {
  return (
    <div className="drawing-toolbar">
      {/* Cursor - always active */}
      <IconButton active tooltip="Cursor">
        <MousePointer2 size={18} />
      </IconButton>

      <div className="toolbar-divider" />

      {/* Scroll to latest candle */}
      <IconButton tooltip="Go to Latest" onClick={onScrollToLatest}>
        <RefreshCw size={18} />
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
