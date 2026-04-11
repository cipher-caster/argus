"use client";

import { useSignalOutcomeTrend } from "@/hooks/useAnalyticsData";
import { SignalOutcomeTrendPoint } from "@/lib/api";
import { TrendingUp, TrendingDown, Minus, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMemo } from "react";

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00Z");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
}

function avg(values: (number | null)[]): number | null {
  const nums = values.filter((v): v is number => v !== null);
  if (nums.length === 0) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

interface SVGLineChartProps {
  trend: SignalOutcomeTrendPoint[];
  width?: number;
  height?: number;
}

function SVGLineChart({ trend, width = 800, height = 260 }: SVGLineChartProps) {
  const PAD = { top: 16, right: 24, bottom: 40, left: 44 };
  const chartW = width - PAD.left - PAD.right;
  const chartH = height - PAD.top - PAD.bottom;

  const n = trend.length;
  if (n < 2) return null;

  const toY = (v: number) => PAD.top + chartH - (v / 100) * chartH;
  const toX = (i: number) => PAD.left + (i / (n - 1)) * chartW;

  const overallPoints = trend
    .map((pt, i) => (pt.win_rate !== null ? `${toX(i)},${toY(pt.win_rate)}` : null))
    .filter(Boolean)
    .join(" ");

  const labelStep = Math.max(1, Math.floor(n / 6));
  const xLabels = trend
    .map((pt, i) => ({ i, label: formatDate(pt.date) }))
    .filter(({ i }) => i === 0 || i === n - 1 || i % labelStep === 0);

  const yTicks = [0, 25, 50, 75, 100];

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      style={{ height }}
      preserveAspectRatio="none"
    >
      {yTicks.map((tick) => (
        <g key={tick}>
          <line
            x1={PAD.left}
            y1={toY(tick)}
            x2={PAD.left + chartW}
            y2={toY(tick)}
            stroke={tick === 50 ? "rgba(255,255,255,0.25)" : "rgba(255,255,255,0.07)"}
            strokeWidth={tick === 50 ? 1.5 : 1}
            strokeDasharray={tick === 50 ? "5,4" : undefined}
          />
          <text x={PAD.left - 8} y={toY(tick) + 4} textAnchor="end" fontSize={10} fill="rgba(255,255,255,0.4)">
            {tick}%
          </text>
        </g>
      ))}

      {xLabels.map(({ i, label }) => (
        <text key={i} x={toX(i)} y={height - 4} textAnchor="middle" fontSize={10} fill="rgba(255,255,255,0.4)">
          {label}
        </text>
      ))}

      {overallPoints && (
        <polyline
          points={overallPoints}
          fill="none"
          stroke="#818cf8"
          strokeWidth={2.5}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      )}

      {trend[n - 1].win_rate !== null && (
        <circle
          cx={toX(n - 1)}
          cy={toY(trend[n - 1].win_rate!)}
          r={4}
          fill="#818cf8"
          stroke="var(--background, #0f0f0f)"
          strokeWidth={2}
        />
      )}
    </svg>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-secondary/30 border border-border/50 rounded-2xl p-4 space-y-1 text-center">
      <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{label}</p>
      <p className="text-xl font-black tabular-nums">{value}</p>
      {sub && <p className="text-[10px] text-muted-foreground font-medium">{sub}</p>}
    </div>
  );
}

export function WinRateTrend() {
  const { data, isLoading } = useSignalOutcomeTrend({ days: 30 });

  const trend = data?.trend ?? [];

  const stats = useMemo(() => {
    if (trend.length === 0) return null;

    const allRates = trend.map((p) => p.win_rate).filter((v): v is number => v !== null);
    const avg30 = avg(allRates);
    const best = allRates.length > 0 ? Math.max(...allRates) : null;
    const bestDate = best !== null ? trend.find((p) => p.win_rate === best)?.date : null;

    const last7 = avg(trend.slice(-7).map((p) => p.win_rate));
    const prior7 = avg(trend.slice(-14, -7).map((p) => p.win_rate));

    let direction: "up" | "down" | "flat" = "flat";
    if (last7 !== null && prior7 !== null) {
      if (last7 - prior7 > 1) direction = "up";
      else if (prior7 - last7 > 1) direction = "down";
    }

    return { avg30, best, bestDate, last7, prior7, direction };
  }, [trend]);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-6 w-48 bg-secondary/40 rounded" />
        <div className="grid grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => <div key={i} className="h-20 bg-secondary/30 rounded-2xl" />)}
        </div>
        <div className="h-64 bg-secondary/20 rounded-2xl" />
      </div>
    );
  }

  if (trend.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-72 text-center space-y-3">
        <BarChart2 size={36} className="text-muted-foreground/40" />
        <p className="font-black text-sm uppercase tracking-widest">No snapshot data yet</p>
        <p className="text-xs text-muted-foreground max-w-xs leading-relaxed">
          Snapshots populate daily at 00:05 UTC. Check back tomorrow after the first daily job run.
        </p>
      </div>
    );
  }

  const trendIcon =
    stats?.direction === "up" ? <TrendingUp size={14} className="text-green-400" /> :
    stats?.direction === "down" ? <TrendingDown size={14} className="text-red-400" /> :
    <Minus size={14} className="text-muted-foreground" />;

  const trendLabel =
    stats?.direction === "up" ? "Trending up" :
    stats?.direction === "down" ? "Trending down" :
    "Flat trend";

  const trendSub =
    stats?.last7 !== null && stats?.prior7 !== null
      ? `Last 7d avg ${stats!.last7!.toFixed(1)}% vs prior ${stats!.prior7!.toFixed(1)}%`
      : "Insufficient data for trend";

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
          <BarChart2 size={16} className="text-primary" />
          Win Rate Trend
        </h3>
        <p className="text-[11px] text-muted-foreground mt-0.5">
          Daily snapshot win-rate over the last 30 days
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="30d avg win rate"
          value={stats?.avg30 != null ? `${stats.avg30.toFixed(1)}%` : "—"}
          sub={`across ${trend.reduce((s, p) => s + p.total_resolved, 0)} resolved signals`}
        />
        <StatCard
          label="Best day"
          value={stats?.best != null ? `${stats.best.toFixed(1)}%` : "—"}
          sub={stats?.bestDate ? formatDate(stats.bestDate) : undefined}
        />
        <div className="bg-secondary/30 border border-border/50 rounded-2xl p-4 space-y-1 text-center">
          <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">7d trend</p>
          <p className={cn(
            "text-xl font-black tabular-nums flex items-center justify-center gap-1.5",
            stats?.direction === "up" ? "text-green-400" : stats?.direction === "down" ? "text-red-400" : ""
          )}>
            {trendIcon}
            {trendLabel}
          </p>
          <p className="text-[10px] text-muted-foreground font-medium">{trendSub}</p>
        </div>
      </div>

      <div className="bg-secondary/20 rounded-2xl border border-border/40 p-4 overflow-hidden">
        <SVGLineChart trend={trend} width={800} height={260} />
      </div>

      <p className="text-[10px] text-muted-foreground/50 text-center font-medium">
        Dashed line at 50% — breakeven threshold.
      </p>
    </div>
  );
}
