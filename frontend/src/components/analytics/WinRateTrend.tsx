"use client";

import { useSignalOutcomeTrend } from "@/hooks/useAnalyticsData";
import { SignalOutcomeTrendPoint } from "@/lib/api";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus, BarChart2 } from "lucide-react";
import { useState, useMemo } from "react";

type Breakdown = "Regime" | "Conviction" | "Source";

const BREAKDOWN_OPTIONS: Breakdown[] = ["Regime", "Conviction", "Source"];

// Map breakdown pill to the fetch param key
const BREAKDOWN_PARAM: Record<Breakdown, keyof { regime?: string; conviction_band?: string; source?: string }> = {
  Regime: "regime",
  Conviction: "conviction_band",
  Source: "source",
};

// Colours per breakdown key value
const LINE_COLORS: Record<string, string> = {
  // Regime
  BULL: "#22c55e",
  BEAR: "#ef4444",
  NEUTRAL: "#a855f7",
  // Conviction bands
  "75+": "#22c55e",
  "65-74": "#eab308",
  "55-64": "#f97316",
  // Sources
  live: "#38bdf8",
  scanner: "#a78bfa",
  backtest: "#fb923c",
};

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
  breakdownLines: Record<string, number | null>[];
  breakdownKeys: string[];
  width?: number;
  height?: number;
}

function SVGLineChart({ trend, breakdownLines, breakdownKeys, width = 800, height = 260 }: SVGLineChartProps) {
  const PAD = { top: 16, right: 24, bottom: 40, left: 44 };
  const chartW = width - PAD.left - PAD.right;
  const chartH = height - PAD.top - PAD.bottom;

  const n = trend.length;
  if (n < 2) return null;

  // Y axis: 0–100
  const yMin = 0;
  const yMax = 100;
  const toY = (v: number) => PAD.top + chartH - ((v - yMin) / (yMax - yMin)) * chartH;
  const toX = (i: number) => PAD.left + (i / (n - 1)) * chartW;

  // Build polyline points for overall win_rate line
  const overallPoints = trend
    .map((pt, i) => (pt.win_rate !== null ? `${toX(i)},${toY(pt.win_rate)}` : null))
    .filter(Boolean)
    .join(" ");

  // Build breakdown lines (one per key)
  const bdPolylines: { key: string; points: string }[] = breakdownKeys.map((key) => {
    const pts = breakdownLines
      .map((row, i) => {
        const v = row[key];
        return v !== null && v !== undefined ? `${toX(i)},${toY(v)}` : null;
      })
      .filter(Boolean)
      .join(" ");
    return { key, points: pts };
  });

  // X-axis labels: show every ~7th point or fewer if small dataset
  const labelStep = Math.max(1, Math.floor(n / 6));
  const xLabels = trend
    .map((pt, i) => ({ i, label: formatDate(pt.date) }))
    .filter(({ i }) => i === 0 || i === n - 1 || i % labelStep === 0);

  // Y-axis gridlines
  const yTicks = [0, 25, 50, 75, 100];

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      style={{ height }}
      preserveAspectRatio="none"
    >
      {/* Gridlines */}
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
          <text
            x={PAD.left - 8}
            y={toY(tick) + 4}
            textAnchor="end"
            fontSize={10}
            fill="rgba(255,255,255,0.4)"
          >
            {tick}%
          </text>
        </g>
      ))}

      {/* X-axis labels */}
      {xLabels.map(({ i, label }) => (
        <text
          key={i}
          x={toX(i)}
          y={height - 4}
          textAnchor="middle"
          fontSize={10}
          fill="rgba(255,255,255,0.4)"
        >
          {label}
        </text>
      ))}

      {/* Breakdown lines (drawn under overall) */}
      {bdPolylines.map(({ key, points }) =>
        points ? (
          <polyline
            key={key}
            points={points}
            fill="none"
            stroke={LINE_COLORS[key] ?? "#6b7280"}
            strokeWidth={1.5}
            strokeOpacity={0.7}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ) : null
      )}

      {/* Overall win-rate line */}
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

      {/* Dots on overall line for latest point */}
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
  const [activeBreakdown, setActiveBreakdown] = useState<Breakdown>("Regime");

  const { data, isLoading } = useSignalOutcomeTrend({ days: 30 });

  const trend = data?.trend ?? [];

  // Compute stat cards
  const stats = useMemo(() => {
    if (trend.length === 0) return null;

    const allRates = trend.map((p) => p.win_rate).filter((v): v is number => v !== null);
    const avg30 = avg(allRates);

    const best = allRates.length > 0 ? Math.max(...allRates) : null;
    const bestDate = best !== null ? trend.find((p) => p.win_rate === best)?.date : null;

    // Last 7 vs prior 7
    const last7 = avg(trend.slice(-7).map((p) => p.win_rate));
    const prior7 = avg(trend.slice(-14, -7).map((p) => p.win_rate));

    let direction: "up" | "down" | "flat" = "flat";
    if (last7 !== null && prior7 !== null) {
      if (last7 - prior7 > 1) direction = "up";
      else if (prior7 - last7 > 1) direction = "down";
    }

    return { avg30, best, bestDate, last7, prior7, direction };
  }, [trend]);

  // Build breakdown lines from the response
  const { breakdownKeys, breakdownLines } = useMemo(() => {
    if (!data || trend.length === 0) return { breakdownKeys: [], breakdownLines: [] };

    const source: Record<string, number> =
      activeBreakdown === "Regime"
        ? data.regime_breakdown
        : activeBreakdown === "Conviction"
        ? data.conviction_breakdown
        : {}; // Source breakdown not provided by backend aggregate, skip

    const keys = Object.keys(source);

    // The breakdown values are aggregate win-rates, not per-day — represent as flat lines
    const lines: Record<string, number | null>[] = trend.map(() =>
      Object.fromEntries(keys.map((k) => [k, source[k] ?? null]))
    );

    return { breakdownKeys: keys, breakdownLines: lines };
  }, [data, activeBreakdown, trend]);

  // ---- Loading skeleton ----
  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-6 w-48 bg-secondary/40 rounded" />
        <div className="grid grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-20 bg-secondary/30 rounded-2xl" />
          ))}
        </div>
        <div className="h-64 bg-secondary/20 rounded-2xl" />
      </div>
    );
  }

  // ---- Empty state ----
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
    stats?.direction === "up" ? (
      <TrendingUp size={14} className="text-green-400" />
    ) : stats?.direction === "down" ? (
      <TrendingDown size={14} className="text-red-400" />
    ) : (
      <Minus size={14} className="text-muted-foreground" />
    );

  const trendLabel =
    stats?.direction === "up"
      ? "Trending up"
      : stats?.direction === "down"
      ? "Trending down"
      : "Flat trend";

  const trendSub =
    stats !== null && stats?.last7 !== null && stats?.prior7 !== null
      ? `Last 7d avg ${stats!.last7!.toFixed(1)}% vs prior ${stats!.prior7!.toFixed(1)}%`
      : "Insufficient data for trend";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
            <BarChart2 size={16} className="text-primary" />
            Win Rate Trend
          </h3>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            Daily snapshot win-rate over the last 30 days
          </p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="30d avg win rate"
          value={stats?.avg30 !== null && stats?.avg30 !== undefined ? `${stats.avg30.toFixed(1)}%` : "—"}
          sub={`across ${trend.reduce((s, p) => s + p.total_resolved, 0)} resolved signals`}
        />
        <StatCard
          label="Best day"
          value={stats?.best !== null && stats?.best !== undefined ? `${stats.best.toFixed(1)}%` : "—"}
          sub={stats?.bestDate ? formatDate(stats.bestDate) : undefined}
        />
        <div className="bg-secondary/30 border border-border/50 rounded-2xl p-4 space-y-1 text-center">
          <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">7d trend</p>
          <p className="text-xl font-black tabular-nums flex items-center justify-center gap-1.5">
            {trendIcon}
            <span
              className={cn(
                stats?.direction === "up" ? "text-green-400" : stats?.direction === "down" ? "text-red-400" : ""
              )}
            >
              {trendLabel}
            </span>
          </p>
          <p className="text-[10px] text-muted-foreground font-medium">{trendSub}</p>
        </div>
      </div>

      {/* Breakdown filter pills */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Breakdown:</span>
        <div className="flex gap-1.5">
          {BREAKDOWN_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => setActiveBreakdown(opt)}
              className={cn(
                "px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide transition-all duration-200",
                activeBreakdown === opt
                  ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                  : "bg-secondary/40 text-muted-foreground hover:bg-secondary/70 hover:text-foreground border border-border/40"
              )}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* Legend */}
      {breakdownKeys.length > 0 && (
        <div className="flex flex-wrap gap-3">
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-6 h-0.5 bg-indigo-400 rounded" />
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide">Overall</span>
          </div>
          {breakdownKeys.map((key) => (
            <div key={key} className="flex items-center gap-1.5">
              <span
                className="inline-block w-6 h-0.5 rounded"
                style={{ backgroundColor: LINE_COLORS[key] ?? "#6b7280" }}
              />
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide">{key}</span>
            </div>
          ))}
        </div>
      )}

      {/* SVG Chart */}
      <div className="bg-secondary/20 rounded-2xl border border-border/40 p-4 overflow-hidden">
        <SVGLineChart
          trend={trend}
          breakdownLines={breakdownLines}
          breakdownKeys={breakdownKeys}
          width={800}
          height={260}
        />
      </div>

      <p className="text-[10px] text-muted-foreground/50 text-center font-medium">
        Dashed line at 50% — breakeven threshold. Breakdown lines show aggregate win-rate per category.
      </p>
    </div>
  );
}
