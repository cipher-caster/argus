"use client";

/**
 * Controls for the liquidation heatmap page
 */

import { RefreshCw } from "lucide-react";

interface LiquidationControlsProps {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
  symbols: string[];
  lookbackHours: number;
  onLookbackChange: (hours: number) => void;
  threshold: number;
  onThresholdChange: (threshold: number) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

const LOOKBACK_OPTIONS = [
  { value: 1, label: "1h" },
  { value: 4, label: "4h" },
  { value: 12, label: "12h" },
  { value: 24, label: "24h" },
];

export function LiquidationControls({ symbol, onSymbolChange, symbols, lookbackHours, onLookbackChange, threshold, onThresholdChange, onRefresh, isRefreshing }: LiquidationControlsProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-secondary/30 rounded-xl border border-border/50">
      {/* Symbol Selector */}
      <div className="flex items-center gap-2">
        <label className="text-xs font-medium text-muted-foreground">Pair</label>
        <select value={symbol} onChange={(e) => onSymbolChange(e.target.value)} className="px-3 py-1.5 bg-background border border-border rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary">
          {symbols.map((s) => (
            <option key={s} value={s}>
              {s.replace("USDT", "/USDT")}
            </option>
          ))}
        </select>
      </div>

      {/* Timeframe Selector */}
      <div className="flex items-center gap-2">
        <label className="text-xs font-medium text-muted-foreground">Lookback</label>
        <div className="flex bg-muted/30 p-1 rounded-lg">
          {LOOKBACK_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onLookbackChange(opt.value)}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${lookbackHours === opt.value ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Threshold Slider */}
      <div className="flex items-center gap-2 flex-1 min-w-[200px]">
        <label className="text-xs font-medium text-muted-foreground whitespace-nowrap">Liquidity Threshold</label>
        <input type="range" min="0" max="1" step="0.05" value={threshold} onChange={(e) => onThresholdChange(parseFloat(e.target.value))} className="flex-1 h-1.5 rounded-full appearance-none bg-muted cursor-pointer accent-primary" />
        <span className="text-xs font-mono text-muted-foreground w-10">{threshold.toFixed(2)}</span>
      </div>

      {/* Refresh Button */}
      <button onClick={onRefresh} disabled={isRefreshing} className="p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors disabled:opacity-50">
        <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
      </button>
    </div>
  );
}
