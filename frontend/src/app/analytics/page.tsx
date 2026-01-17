"use client";

import { ContrarianRadar, LiquidityMap, MarketHealth, OracleScreener, RelativeStrength } from "@/components/analytics";
import { cn } from "@/lib/utils";
import { Activity, Droplets, Gauge, Info, LayoutGrid, TrendingUp } from "lucide-react";
import { useState } from "react";

type ChartType = "screener" | "market-health" | "liquidity-sweeps" | "contrarian-radar" | "relative-strength";

const MENU_ITEMS: { id: ChartType; label: string; icon: any }[] = [
  { id: "screener", label: "Oracle Screener", icon: LayoutGrid },
  { id: "market-health", label: "Market Health", icon: Activity },
  { id: "liquidity-sweeps", label: "Liquidity Map", icon: Droplets },
  { id: "contrarian-radar", label: "Contrarian Radar", icon: Gauge },
  { id: "relative-strength", label: "Relative Strength", icon: TrendingUp },
];

const CHART_INFO: Record<ChartType, { title: string; description: string }> = {
  screener: {
    title: "Oracle Screener",
    description: "Real-time AI analysis across the top 50 perpetual markets. Identifies trend alignment, momentum scores, and high-probability setups.",
  },
  "market-health": {
    title: "Market Health",
    description: "Aggregate sentiment metrics. Monitors what percentage of the market is trending bullish (above 200D EMA) and detects institutional volatility squeezes.",
  },
  "liquidity-sweeps": {
    title: "Liquidity Map",
    description: "Detects stop-run and reclaim patterns (SFP). Identifies levels where smart money has engineered liquidity before a reversal.",
  },
  "contrarian-radar": {
    title: "Contrarian Radar",
    description: "Monitors extreme ATR extensions. Identifies pairs that are overstretched from their mean (EMA) and due for a mean-reversion move.",
  },
  "relative-strength": {
    title: "Relative Strength",
    description: "Compares altcoin performance directly against Bitcoin. Identifies true 'Alpha' leaders that are outperforming the market benchmark.",
  },
};

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<ChartType>("screener");
  const [timeframe, setTimeframe] = useState<string>("1h");

  const TIMEFRAMES = [
    { id: "1h", label: "1H", description: "Intraday Momentum" },
    { id: "4h", label: "4H", description: "Swing Trends" },
    { id: "1d", label: "1D", description: "Daily Exhaustion" },
  ];

  const info = CHART_INFO[activeTab];

  return (
    <main className="max-w-[1440px] mx-auto p-6 md:p-8 space-y-10 min-h-screen">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 animate-in fade-in slide-in-from-top-2 duration-500">
        <div className="space-y-2">
          <h1 className="text-3xl font-black tracking-tight flex items-center gap-3 italic">QUANT ANALYTICS</h1>
          <p className="text-muted-foreground text-sm font-medium tracking-wide uppercase opacity-70">Professional-grade market intelligence and automated screening.</p>
        </div>

        {/* Global Timeframe Selector */}
        <div className="flex bg-secondary/30 p-1 rounded-xl border border-border/50 backdrop-blur-sm self-start md:self-auto">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.id}
              onClick={() => setTimeframe(tf.id)}
              className={cn(
                "px-4 py-2 rounded-lg text-[11px] font-black uppercase tracking-wider transition-all duration-300",
                timeframe === tf.id ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" : "text-muted-foreground hover:text-foreground hover:bg-white/5",
              )}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start animate-in fade-in slide-in-from-bottom-4 duration-700">
        {/* Navigation Sidebar */}
        <aside className="lg:col-span-1 space-y-4 sticky top-8">
          <nav className="bg-secondary/30 rounded-2xl p-2 border border-border/50 backdrop-blur-sm">
            {MENU_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-300 group relative overflow-hidden",
                  activeTab === item.id ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" : "hover:bg-primary/10 text-muted-foreground hover:text-foreground hover:translate-x-1",
                )}
              >
                {activeTab === item.id && <div className="absolute left-0 top-0 bottom-0 w-1 bg-white/20" />}
                <item.icon size={18} className={cn("transition-transform duration-300", activeTab === item.id ? "scale-110" : "group-hover:scale-110")} />
                <span className="text-[13px] font-bold uppercase tracking-tight">{item.label}</span>
              </button>
            ))}
          </nav>

          {/* Info Card */}
          <div className="bg-secondary/30 rounded-2xl p-5 border border-border/50 space-y-3 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-primary">
              <Info size={16} />
              <h3 className="text-xs font-black uppercase tracking-widest">{info.title}</h3>
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed font-medium">{info.description}</p>
          </div>
        </aside>

        {/* Content Area */}
        <div className="lg:col-span-3 min-h-[700px] bg-secondary/10 rounded-3xl border border-border/30 overflow-hidden shadow-2xl shadow-black/20">
          <div className="p-6 md:p-8">
            {activeTab === "screener" && <OracleScreener timeframe={timeframe} />}
            {activeTab === "market-health" && <MarketHealth timeframe={timeframe} />}
            {activeTab === "liquidity-sweeps" && <LiquidityMap timeframe={timeframe} />}
            {activeTab === "contrarian-radar" && <ContrarianRadar timeframe={timeframe} />}
            {activeTab === "relative-strength" && <RelativeStrength timeframe={timeframe} />}
          </div>
        </div>
      </div>
    </main>
  );
}
