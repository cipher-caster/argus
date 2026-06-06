"use client";

import { IndicatorConfig } from "@/stores/indicatorStore";
import { RefCallback } from "react";

interface IndicatorPaneProps {
  config: IndicatorConfig;
  onContainerRef: RefCallback<HTMLDivElement>;
}

export function IndicatorPane({ config, onContainerRef }: IndicatorPaneProps) {
  return (
    <div className="flex flex-col flex-shrink-0 bg-card border-t border-border">
      <div className="flex items-center gap-2 px-3 py-1.5 bg-muted/30 border-b border-border">
        <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: config.color }}>
          {config.displayName}
        </span>
      </div>
      <div ref={onContainerRef} className="w-full h-[120px] flex-shrink-0" />
    </div>
  );
}
