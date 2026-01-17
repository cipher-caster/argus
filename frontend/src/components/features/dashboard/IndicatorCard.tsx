"use client";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { HelpCircle } from "lucide-react";
import { memo, useMemo } from "react";

interface GaugeBarProps {
  value: number;
  min?: number;
  max?: number;
  lowColor?: string;
  highColor?: string;
}

/**
 * Gradient gauge bar (Fear→Greed or Low→High style)
 */
function GaugeBar({ value, min = 0, max = 100, lowColor = "#ef4444", highColor = "#22c55e" }: GaugeBarProps) {
  const position = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));

  return (
    <div className="relative w-full h-2 rounded-full overflow-hidden">
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: `linear-gradient(to right, ${lowColor}, #eab308, ${highColor})`,
        }}
      />
      <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 border-gray-800 shadow-md transition-all duration-500" style={{ left: `calc(${position}% - 6px)` }} />
    </div>
  );
}

interface AreaSparklineProps {
  data: number[];
  color?: string;
  height?: number;
}

/**
 * Area chart sparkline for indicator history
 */
function AreaSparkline({ data, color = "#22c55e", height = 48 }: AreaSparklineProps) {
  const pathData = useMemo(() => {
    if (!data || data.length < 2) return { line: "", area: "" };

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const width = 100;

    const points = data.map((val, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * height;
      return { x, y };
    });

    const line = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x},${p.y}`).join(" ");
    const area = `${line} L ${width},${height} L 0,${height} Z`;

    return { line, area };
  }, [data, height]);

  if (!data || data.length < 2) {
    return (
      <div style={{ height }} className="flex items-center justify-center text-muted-foreground text-xs">
        No data
      </div>
    );
  }

  return (
    <svg width="100%" height={height} viewBox={`0 0 100 ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0.05" />
        </linearGradient>
      </defs>
      <path d={pathData.area} fill={`url(#gradient-${color})`} />
      <path d={pathData.line} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export interface IndicatorCardProps {
  title: string;
  icon?: React.ReactNode;
  value: number | string;
  label?: string;
  subtitle?: string;
  tooltip?: string;
  min?: number;
  max?: number;
  history?: number[];
  showGauge?: boolean;
  gaugeColors?: { low: string; high: string };
  chartColor?: string;
  extraContent?: React.ReactNode;
}

function IndicatorCardComponent({ title, icon, value, label, subtitle, tooltip, min, max, history = [], showGauge = false, gaugeColors = { low: "#ef4444", high: "#22c55e" }, chartColor = "#22c55e", extraContent }: IndicatorCardProps) {
  const displayValue = typeof value === "number" ? value.toFixed(1) : value;

  const labelColorClass = useMemo(() => {
    if (!label) return "";
    const l = label.toLowerCase();
    if (l.includes("low") || l.includes("ranging") || l.includes("neutral")) return "text-cyan-400";
    if (l.includes("high") || l.includes("strong") || l.includes("bullish")) return "text-green-400";
    if (l.includes("extreme") || l.includes("bearish")) return "text-red-400";
    if (l.includes("medium") || l.includes("trending") || l.includes("normal")) return "text-yellow-400";
    return "text-muted-foreground";
  }, [label]);

  return (
    <div className="bg-secondary border border-border rounded-xl p-4 flex-1 min-w-[260px] shadow-sm hover:shadow-lg transition-all duration-300 group">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {icon && <span className="text-muted-foreground">{icon}</span>}
          <span className="text-[13px] text-muted-foreground font-bold uppercase tracking-tight">{title}</span>
        </div>
        {tooltip && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button className="p-1 rounded-md text-muted-foreground hover:text-foreground transition-colors">
                  <HelpCircle size={14} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[250px] text-center">
                <p>{tooltip}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      {/* Value Display */}
      <div className="flex items-baseline gap-2 mb-2">
        <span className={cn("text-3xl font-extrabold tracking-tighter leading-none", labelColorClass || "text-foreground")}>{displayValue}</span>
        {label && <span className={cn("text-sm font-semibold", labelColorClass)}>{label}</span>}
      </div>
      {subtitle && <div className="text-xs text-muted-foreground mb-2">{subtitle}</div>}

      {/* Gauge Bar */}
      {showGauge && (
        <div className="mb-3">
          <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
            <span>Low</span>
            <span>High</span>
          </div>
          <GaugeBar value={typeof value === "number" ? value : 50} min={min ?? 0} max={max ?? 100} lowColor={gaugeColors.low} highColor={gaugeColors.high} />
        </div>
      )}

      {/* Extra Content (e.g., percentage changes) */}
      {extraContent}

      {/* Sparkline Chart */}
      {history.length > 0 && (
        <div className="mt-2">
          <AreaSparkline data={history} color={chartColor} height={40} />
          {min !== undefined && max !== undefined && (
            <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
              <span>Min: {typeof min === "number" && min > 1000 ? `$${(min / 1e12).toFixed(2)}T` : min?.toFixed(1)}</span>
              <span>Max: {typeof max === "number" && max > 1000 ? `$${(max / 1e12).toFixed(2)}T` : max?.toFixed(1)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export const IndicatorCard = memo(IndicatorCardComponent);
