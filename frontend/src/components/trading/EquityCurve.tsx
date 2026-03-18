"use client";

import { useTradingStats } from "@/hooks/useTradingData";
import { cn } from "@/lib/utils";

function formatTs(ms: number) {
  return new Date(ms).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function EquityCurve() {
  const { data: stats, isLoading } = useTradingStats();

  if (isLoading) {
    return (
      <div className="bg-card/60 border border-border/40 rounded-2xl p-4 h-40 animate-pulse" />
    );
  }

  const curve = stats?.equity_curve ?? [];
  const initialCapital = stats ? (stats.balance - stats.total_pnl_usd) : 100;

  if (curve.length === 0) {
    return (
      <div className="bg-card/60 backdrop-blur-md border border-border/40 rounded-2xl p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-black tracking-tight">Equity Curve</h3>
          <span className="text-[10px] text-muted-foreground">No trades yet</span>
        </div>
        <div className="h-28 flex items-center justify-center text-muted-foreground text-xs">
          Equity curve will appear after the first closed trade
        </div>
      </div>
    );
  }

  // Build SVG path
  const values = [initialCapital, ...curve.map(p => p.balance)];
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;

  const W = 600;
  const H = 120;
  const PAD = 8;

  function toX(i: number) {
    return PAD + ((i) / (values.length - 1)) * (W - PAD * 2);
  }
  function toY(v: number) {
    return H - PAD - ((v - minVal) / range) * (H - PAD * 2);
  }

  const points = values.map((v, i) => `${toX(i)},${toY(v)}`).join(" ");
  const linePath = `M ${values.map((v, i) => `${toX(i)} ${toY(v)}`).join(" L ")}`;
  const areaPath = `${linePath} L ${toX(values.length - 1)} ${H} L ${toX(0)} ${H} Z`;

  const isPositive = values[values.length - 1] >= initialCapital;
  const color = isPositive ? "#10b981" : "#ef4444";
  const colorDim = isPositive ? "rgba(16,185,129,0.15)" : "rgba(239,68,68,0.15)";

  const currentBalance = curve[curve.length - 1]?.balance ?? initialCapital;
  const totalPnl = currentBalance - initialCapital;
  const totalPct = (totalPnl / initialCapital) * 100;

  return (
    <div className="bg-card/60 backdrop-blur-md border border-border/40 rounded-2xl p-4 overflow-hidden">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-black tracking-tight">Equity Curve</h3>
        <div className="flex items-center gap-3">
          <span className={cn(
            "text-[12px] font-black",
            isPositive ? "text-emerald-500" : "text-red-500"
          )}>
            {totalPnl >= 0 ? "+" : ""}${totalPnl.toFixed(2)} ({totalPct >= 0 ? "+" : ""}{totalPct.toFixed(1)}%)
          </span>
          <span className="text-[10px] text-muted-foreground">{curve.length} trades</span>
        </div>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 120 }}>
        <defs>
          <linearGradient id="ec-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Area fill */}
        <path d={areaPath} fill="url(#ec-gradient)" />
        {/* Line */}
        <path d={linePath} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
        {/* Dots for each trade */}
        {curve.map((pt, i) => (
          <circle
            key={i}
            cx={toX(i + 1)}
            cy={toY(pt.balance)}
            r="2.5"
            fill={pt.outcome === "WIN" ? "#10b981" : pt.outcome === "LOSS" ? "#ef4444" : "#6b7280"}
          />
        ))}
      </svg>

      {/* X axis labels */}
      {curve.length > 1 && (
        <div className="flex justify-between text-[9px] text-muted-foreground mt-1 px-1">
          <span>{formatTs(curve[0].timestamp ?? 0)}</span>
          <span>{formatTs(curve[curve.length - 1].timestamp ?? 0)}</span>
        </div>
      )}
    </div>
  );
}
