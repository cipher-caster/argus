"use client";

import { DrawingToolbar as DrawingTools } from "@/components/drawing";
import { IconButton } from "@/components/ui";
import { RefreshCw } from "lucide-react";

interface DrawingToolbarProps {
  symbol: string;
  onScrollToLatest?: () => void;
}

export function DrawingToolbar({ symbol, onScrollToLatest }: DrawingToolbarProps) {
  return (
    <div className="relative h-full">
      <DrawingTools symbol={symbol} />
      <div className="absolute bottom-2 left-0 right-0 flex justify-center">
        <IconButton tooltip="Go to Latest" onClick={onScrollToLatest}>
          <RefreshCw size={18} />
        </IconButton>
      </div>
    </div>
  );
}
