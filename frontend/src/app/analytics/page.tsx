"use client";

/**
 * Analytics Page - Futures market data charts
 * CoinGlass-style layout with sidebar menu and chart area
 */

import { useAnalyticsSymbols, useFundingRate, useLongShortRatio, useOpenInterest } from "@/hooks/useAnalyticsData";
import { cn } from "@/lib/utils";
import { BarChart3, Info, RefreshCw, TrendingUp, Users } from "lucide-react";
import { useState } from "react";

type ChartType = "funding-rate" | "open-interest" | "long-short-ratio";

const MENU_ITEMS = [
  { id: "funding-rate" as ChartType, label: "Funding Rate", icon: TrendingUp },
  { id: "open-interest" as ChartType, label: "Open Interest", icon: BarChart3 },
  { id: "long-short-ratio" as ChartType, label: "Long/Short Ratio", icon: Users },
];

const PERIOD_OPTIONS = [
  { value: "5m", label: "5m" },
  { value: "15m", label: "15m" },
  { value: "1h", label: "1h" },
  { value: "4h", label: "4h" },
  { value: "1d", label: "1D" },
];

// Educational descriptions for each chart type
const CHART_INFO = {
  "funding-rate": {
    title: "What is Funding Rate?",
    description: "Funding rates are periodic payments between long and short traders in perpetual futures. When positive (green), longs pay shorts - indicating bullish sentiment. When negative (red), shorts pay longs - indicating bearish sentiment.",
    tips: ["Consistently positive rates suggest market is overleveraged long", "Negative rates during uptrends can signal healthy corrections", "Extreme rates (>0.1%) often precede reversals"],
  },
  "open-interest": {
    title: "What is Open Interest?",
    description: "Open Interest represents the total value of outstanding futures contracts. Rising OI with rising price indicates new money entering bullish positions. Falling OI suggests positions are being closed.",
    tips: ["Rising price + Rising OI = Strong bullish trend", "Rising price + Falling OI = Weak rally (shorts covering)", "Falling price + Rising OI = Strong bearish trend"],
  },
  "long-short-ratio": {
    title: "What is Long/Short Ratio?",
    description: "Shows the percentage of accounts holding long vs short positions. This is a contrarian indicator - when too many traders are on one side, the market often moves against them.",
    tips: ["Extreme readings (>70% one side) often precede reversals", "Use as confirmation, not primary signal", "Smart money often positions opposite to retail"],
  },
};

export default function AnalyticsPage() {
  const [activeChart, setActiveChart] = useState<ChartType>("funding-rate");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [period, setPeriod] = useState("1h");

  const { data: symbolsData } = useAnalyticsSymbols();
  const fundingQuery = useFundingRate(symbol, 200);
  const openInterestQuery = useOpenInterest(symbol, period, 200);
  const longShortQuery = useLongShortRatio(symbol, period, 200);

  const symbols = symbolsData?.symbols || ["BTCUSDT"];

  const getActiveQuery = () => {
    switch (activeChart) {
      case "funding-rate":
        return fundingQuery;
      case "open-interest":
        return openInterestQuery;
      case "long-short-ratio":
        return longShortQuery;
    }
  };

  const activeQuery = getActiveQuery();
  const chartInfo = CHART_INFO[activeChart];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex">
        {/* Left Sidebar */}
        <aside className="w-64 min-h-screen bg-secondary/30 border-r border-border p-4">
          <h2 className="text-lg font-bold mb-4 px-2">Futures Data</h2>

          {/* Symbol Selector */}
          <div className="mb-6">
            <label className="text-xs font-medium text-muted-foreground px-2 mb-2 block">Symbol</label>
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)} className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm font-medium">
              {symbols.map((s) => (
                <option key={s} value={s}>
                  {s.replace("USDT", "/USDT")}
                </option>
              ))}
            </select>
          </div>

          {/* Period Selector (for OI and L/S ratio) */}
          {activeChart !== "funding-rate" && (
            <div className="mb-6">
              <label className="text-xs font-medium text-muted-foreground px-2 mb-2 block">Period</label>
              <div className="flex flex-wrap gap-1 px-2">
                {PERIOD_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setPeriod(opt.value)}
                    className={cn("px-2 py-1 text-xs font-bold rounded-md transition-all", period === opt.value ? "bg-primary text-primary-foreground" : "bg-muted/50 text-muted-foreground hover:bg-muted")}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Menu Items */}
          <nav className="space-y-1">
            {MENU_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveChart(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-left",
                  activeChart === item.id ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <item.icon size={18} />
                {item.label}
              </button>
            ))}
          </nav>

          {/* Info Box */}
          <div className="mt-6 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-blue-500 text-xs font-semibold mb-2">
              <Info size={14} />
              {chartInfo.title}
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">{chartInfo.description}</p>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-extrabold">{MENU_ITEMS.find((m) => m.id === activeChart)?.label}</h1>
              <p className="text-sm text-muted-foreground">{symbol.replace("USDT", "/USDT")} Perpetual</p>
            </div>
            <button onClick={() => activeQuery.refetch()} disabled={activeQuery.isFetching} className="p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
              <RefreshCw size={18} className={activeQuery.isFetching ? "animate-spin" : ""} />
            </button>
          </div>

          {/* Summary Stats */}
          {!activeQuery.isLoading && !activeQuery.error && (
            <div className="mb-4">
              {activeChart === "funding-rate" && fundingQuery.data && <FundingRateSummary data={fundingQuery.data.data} />}
              {activeChart === "open-interest" && openInterestQuery.data && <OpenInterestSummary data={openInterestQuery.data.data} />}
              {activeChart === "long-short-ratio" && longShortQuery.data && <LongShortRatioSummary data={longShortQuery.data.data} />}
            </div>
          )}

          {/* Chart Area */}
          <div className="bg-secondary/30 rounded-2xl border border-border/50 p-6">
            {activeQuery.isLoading ? (
              <div className="h-[500px] flex items-center justify-center text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  Loading...
                </div>
              </div>
            ) : activeQuery.error ? (
              <div className="h-[500px] flex items-center justify-center text-red-500">Error loading data</div>
            ) : (
              <div className="h-[500px]">
                {activeChart === "funding-rate" && fundingQuery.data && <FundingRateChart data={fundingQuery.data.data} />}
                {activeChart === "open-interest" && openInterestQuery.data && <OpenInterestChart data={openInterestQuery.data.data} />}
                {activeChart === "long-short-ratio" && longShortQuery.data && <LongShortRatioChart data={longShortQuery.data.data} />}
              </div>
            )}
          </div>

          {/* Trading Tips */}
          <div className="mt-4 p-4 bg-secondary/30 rounded-xl border border-border/50">
            <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
              <TrendingUp size={14} className="text-primary" />
              Trading Tips
            </h3>
            <ul className="text-xs text-muted-foreground space-y-1">
              {chartInfo.tips.map((tip, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-primary">•</span>
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        </main>
      </div>
    </div>
  );
}

// Summary components
function FundingRateSummary({ data }: { data: { timestamp: number; funding_rate: number }[] }) {
  const sorted = [...data].sort((a, b) => a.timestamp - b.timestamp);
  const latest = sorted[sorted.length - 1];
  const avg = data.reduce((sum, d) => sum + d.funding_rate, 0) / data.length;
  const max = Math.max(...data.map((d) => d.funding_rate));
  const min = Math.min(...data.map((d) => d.funding_rate));

  return (
    <div className="grid grid-cols-4 gap-4">
      <StatCard label="Current Rate" value={`${(latest.funding_rate * 100).toFixed(4)}%`} valueClass={latest.funding_rate >= 0 ? "text-green-500" : "text-red-500"} />
      <StatCard label="Average" value={`${(avg * 100).toFixed(4)}%`} valueClass={avg >= 0 ? "text-green-500" : "text-red-500"} />
      <StatCard label="Highest" value={`${(max * 100).toFixed(4)}%`} valueClass="text-green-500" />
      <StatCard label="Lowest" value={`${(min * 100).toFixed(4)}%`} valueClass="text-red-500" />
    </div>
  );
}

function OpenInterestSummary({ data }: { data: { timestamp: number; open_interest_value: number }[] }) {
  const sorted = [...data].sort((a, b) => a.timestamp - b.timestamp);
  const latest = sorted[sorted.length - 1];
  const first = sorted[0];
  const change = ((latest.open_interest_value - first.open_interest_value) / first.open_interest_value) * 100;
  const max = Math.max(...data.map((d) => d.open_interest_value));

  return (
    <div className="grid grid-cols-4 gap-4">
      <StatCard label="Current OI" value={`$${(latest.open_interest_value / 1e9).toFixed(2)}B`} />
      <StatCard label="Period Change" value={`${change >= 0 ? "+" : ""}${change.toFixed(2)}%`} valueClass={change >= 0 ? "text-green-500" : "text-red-500"} />
      <StatCard label="Period High" value={`$${(max / 1e9).toFixed(2)}B`} />
      <StatCard label="Data Points" value={data.length.toString()} />
    </div>
  );
}

function LongShortRatioSummary({ data }: { data: { timestamp: number; long_account: number; short_account: number }[] }) {
  const sorted = [...data].sort((a, b) => a.timestamp - b.timestamp);
  const latest = sorted[sorted.length - 1];
  const avgLong = data.reduce((sum, d) => sum + d.long_account, 0) / data.length;

  return (
    <div className="grid grid-cols-4 gap-4">
      <StatCard label="Longs" value={`${(latest.long_account * 100).toFixed(1)}%`} valueClass="text-green-500" />
      <StatCard label="Shorts" value={`${(latest.short_account * 100).toFixed(1)}%`} valueClass="text-red-500" />
      <StatCard label="L/S Ratio" value={(latest.long_account / latest.short_account).toFixed(2)} />
      <StatCard label="Avg Long %" value={`${(avgLong * 100).toFixed(1)}%`} />
    </div>
  );
}

function StatCard({ label, value, valueClass = "text-foreground" }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="bg-secondary/50 rounded-lg p-3 border border-border/50">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className={cn("text-lg font-bold font-mono", valueClass)}>{value}</div>
    </div>
  );
}

// Chart components with better sizing

function FundingRateChart({ data }: { data: { timestamp: number; funding_rate: number }[] }) {
  if (!data.length) return <div className="h-full flex items-center justify-center text-muted-foreground">No data</div>;

  const sorted = [...data].sort((a, b) => a.timestamp - b.timestamp);
  const maxRate = Math.max(...sorted.map((d) => Math.abs(d.funding_rate)));

  return (
    <div className="h-full flex flex-col">
      <svg viewBox="0 0 1000 400" className="flex-1 w-full" preserveAspectRatio="none">
        {/* Grid lines */}
        <line x1="0" y1="200" x2="1000" y2="200" stroke="#333" strokeWidth="1" />
        <line x1="0" y1="100" x2="1000" y2="100" stroke="#222" strokeWidth="0.5" strokeDasharray="5,5" />
        <line x1="0" y1="300" x2="1000" y2="300" stroke="#222" strokeWidth="0.5" strokeDasharray="5,5" />

        {/* Bars */}
        {sorted.map((point, i) => {
          const barWidth = 1000 / sorted.length;
          const x = i * barWidth;
          const normalizedRate = point.funding_rate / (maxRate || 0.001);
          const barHeight = Math.abs(normalizedRate) * 180;
          const y = point.funding_rate >= 0 ? 200 - barHeight : 200;
          const color = point.funding_rate >= 0 ? "#22c55e" : "#ef4444";

          return <rect key={i} x={x + barWidth * 0.1} y={y} width={barWidth * 0.8} height={barHeight} fill={color} opacity={0.85} />;
        })}
      </svg>
      <div className="flex justify-between text-xs text-muted-foreground mt-2 px-2">
        <span>{new Date(sorted[0].timestamp).toLocaleString()}</span>
        <span className="text-muted-foreground/50">← 8h intervals →</span>
        <span>{new Date(sorted[sorted.length - 1].timestamp).toLocaleString()}</span>
      </div>
    </div>
  );
}

function OpenInterestChart({ data }: { data: { timestamp: number; open_interest_value: number }[] }) {
  if (!data.length) return <div className="h-full flex items-center justify-center text-muted-foreground">No data</div>;

  const sorted = [...data].sort((a, b) => a.timestamp - b.timestamp);
  const maxOI = Math.max(...sorted.map((d) => d.open_interest_value));
  const minOI = Math.min(...sorted.map((d) => d.open_interest_value));
  const range = maxOI - minOI || 1;

  const points = sorted
    .map((d, i) => {
      const x = (i / (sorted.length - 1)) * 1000;
      const y = 380 - ((d.open_interest_value - minOI) / range) * 360;
      return `${x},${y}`;
    })
    .join(" ");

  // Create area fill
  const areaPoints = `0,380 ${points} 1000,380`;

  return (
    <div className="h-full flex flex-col">
      <svg viewBox="0 0 1000 400" className="flex-1 w-full" preserveAspectRatio="none">
        {/* Grid */}
        {[0.25, 0.5, 0.75].map((pct) => (
          <line key={pct} x1="0" y1={20 + pct * 360} x2="1000" y2={20 + pct * 360} stroke="#222" strokeWidth="0.5" strokeDasharray="5,5" />
        ))}

        {/* Area fill */}
        <polygon points={areaPoints} fill="url(#oiGradient)" opacity="0.3" />

        {/* Line */}
        <polyline points={points} fill="none" stroke="#3b82f6" strokeWidth="2" />

        {/* Gradient definition */}
        <defs>
          <linearGradient id="oiGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>
      <div className="flex justify-between text-xs text-muted-foreground mt-2 px-2">
        <span>{new Date(sorted[0].timestamp).toLocaleString()}</span>
        <span>{new Date(sorted[sorted.length - 1].timestamp).toLocaleString()}</span>
      </div>
    </div>
  );
}

function LongShortRatioChart({ data }: { data: { timestamp: number; long_account: number; short_account: number }[] }) {
  if (!data.length) return <div className="h-full flex items-center justify-center text-muted-foreground">No data</div>;

  const sorted = [...data].sort((a, b) => a.timestamp - b.timestamp);

  return (
    <div className="h-full flex flex-col">
      <svg viewBox="0 0 1000 400" className="flex-1 w-full" preserveAspectRatio="none">
        {/* 50% line */}
        <line x1="0" y1="200" x2="1000" y2="200" stroke="#444" strokeWidth="1" strokeDasharray="5,5" />
        <text x="1010" y="205" fontSize="10" fill="#666">
          50%
        </text>

        {/* Bars */}
        {sorted.map((point, i) => {
          const barWidth = 1000 / sorted.length;
          const x = i * barWidth;
          const longHeight = point.long_account * 400;
          const shortHeight = point.short_account * 400;

          return (
            <g key={i}>
              <rect x={x + barWidth * 0.1} y={0} width={barWidth * 0.8} height={longHeight} fill="#22c55e" opacity={0.8} />
              <rect x={x + barWidth * 0.1} y={longHeight} width={barWidth * 0.8} height={shortHeight} fill="#ef4444" opacity={0.8} />
            </g>
          );
        })}
      </svg>
      <div className="flex justify-between text-xs text-muted-foreground mt-2 px-2">
        <span>{new Date(sorted[0].timestamp).toLocaleString()}</span>
        <div className="flex gap-4">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-sm" /> Longs
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-red-500 rounded-sm" /> Shorts
          </span>
        </div>
        <span>{new Date(sorted[sorted.length - 1].timestamp).toLocaleString()}</span>
      </div>
    </div>
  );
}
