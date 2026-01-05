"use client";

import { IconButton } from "@/components/ui";
import { MousePointer2, RefreshCw } from "lucide-react";

interface DrawingToolbarProps {
  onScrollToLatest?: () => void;
}

export function DrawingToolbar({ onScrollToLatest }: DrawingToolbarProps) {
  return (
    <div className="flex flex-col gap-0.5 py-2 px-1 bg-secondary border-r border-border h-full">
      {/* Cursor - always active */}
      <IconButton active tooltip="Cursor">
        <MousePointer2 size={18} />
      </IconButton>

      <div className="h-px mx-1 my-2 bg-border" />

      {/* Scroll to latest candle */}
      <IconButton tooltip="Go to Latest" onClick={onScrollToLatest}>
        <RefreshCw size={18} />
      </IconButton>
    </div>
  );
}
