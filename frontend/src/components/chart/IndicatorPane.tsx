"use client";

import { IndicatorConfig } from "@/stores/indicatorStore";
import { RefCallback } from "react";

interface IndicatorPaneProps {
  config: IndicatorConfig;
  onContainerRef: RefCallback<HTMLDivElement>;
}

export function IndicatorPane({ config, onContainerRef }: IndicatorPaneProps) {
  return (
    <>
      <div className="indicator-pane-wrapper">
        <div className="indicator-pane-header">
          <span className="indicator-pane-title" style={{ color: config.color }}>
            {config.displayName}
          </span>
        </div>
        <div ref={onContainerRef} className="indicator-pane-chart" />
      </div>

      <style jsx global>{`
        .indicator-pane-wrapper {
          border-top: 1px solid var(--border-color);
          background: var(--chart-bg);
          display: flex;
          flex-direction: column;
          flex-shrink: 0;
        }

        .indicator-pane-header {
          padding: 4px 10px;
          font-size: 11px;
          font-weight: 600;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .indicator-pane-title {
          font-weight: 600;
        }

        .indicator-pane-chart {
          width: 100%;
          height: 120px;
          flex-shrink: 0;
        }
      `}</style>
    </>
  );
}
