"use client";

import { cn } from "@/lib/utils";
import { BarChart2, Gauge, Info, LayoutGrid, Scan, ShieldCheck } from "lucide-react";
import dynamic from "next/dynamic";
import { useState } from "react";

// Lazy load heavy analytics components
const OracleScreener = dynamic(() => import("@/components/analytics").then((mod) => ({ default: mod.OracleScreener })), {
  loading: () => <div className="h-[500px] flex items-center justify-center text-muted-foreground">Loading Oracle Screener...</div>,
});

const ContrarianRadar = dynamic(() => import("@/components/analytics").then((mod) => ({ default: mod.ContrarianRadar })), {
  loading: () => <div className="h-[400px] flex items-center justify-center text-muted-foreground">Loading Contrarian Radar...</div>,
});

const TitanRadar = dynamic(() => import("@/components/analytics").then((mod) => ({ default: mod.TitanRadar })), {
  loading: () => <div className="h-[400px] flex items-center justify-center text-muted-foreground">Loading Titan Radar...</div>,
});

const TitanSignalsPanel = dynamic(() => import("@/components/analytics/TitanSignalsPanel").then((mod) => ({ default: mod.TitanSignalsPanel })), {
  loading: () => <div className="h-[400px] flex items-center justify-center text-muted-foreground">Loading Titan Signals...</div>,
});

const RelativeStrength = dynamic(() => import("@/components/analytics").then((mod) => ({ default: mod.RelativeStrength })), {
  loading: () => <div className="h-[400px] flex items-center justify-center text-muted-foreground">Loading Relative Strength...</div>,
});

type ChartType = "screener" | "contrarian-radar" | "titan-radar" | "titan-signals" | "relative-strength";

const MENU_ITEMS: { id: ChartType; label: string; icon: any }[] = [
  { id: "screener", label: "Oracle Screener", icon: LayoutGrid },
  { id: "titan-signals", label: "Titan Signals (Live)", icon: ShieldCheck },
  { id: "titan-radar", label: "Titan Scanner (Discovery)", icon: Scan },
  { id: "contrarian-radar", label: "Contrarian Radar", icon: Gauge },
  { id: "relative-strength", label: "Relative Strength", icon: BarChart2 },
];

const CHART_INFO: Record<ChartType, { title: string; description: string }> = {
  screener: {
    title: "Oracle Screener",
    description: "Real-time AI analysis across the top 50 perpetual markets. Identifies trend alignment, momentum scores, and high-probability setups.",
  },
  "titan-signals": {
    title: "Titan Signals (Predictive)",
    description: "Your execution dashboard. Uses 'Wait Logic' to prevent chasing pumps and provides specific Limit Entry prices at mathematical supports. Best for setting actual trade orders.",
  },
  "titan-radar": {
    title: "Titan Scanner (Discovery)",
    description: "A bird's-eye view of 50+ assets. Automatically detects trend alignment and momentum breakouts using the Titan hybrid system. Best for finding what to watch.",
  },
  "contrarian-radar": {
    title: "Contrarian Radar",
    description: "Monitors extreme ATR extensions. Identifies pairs that are overstretched from their mean (EMA) and due for a mean-reversion move.",
  },
  "relative-strength": {
    title: "Alpha Leaders",
    description: "Compares each altcoin's performance against Bitcoin. Identifies which coins are showing real alpha — gaining value even when priced in BTC.",
  },
};

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<ChartType>("screener");
  const [timeframe, setTimeframe] = useState<string>("4h");

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
        <div className="lg:col-span-3 min-h-[500px] bg-secondary/10 rounded-3xl border border-border/30 overflow-hidden shadow-2xl shadow-black/20">
          <div className="p-6 md:p-8">
            {activeTab === "screener" && <OracleScreener timeframe={timeframe} />}
            {activeTab === "titan-radar" && <TitanRadar timeframe={timeframe} />}
            {activeTab === "titan-signals" && <TitanSignalsPanel timeframe={timeframe} />}
            {activeTab === "contrarian-radar" && <ContrarianRadar timeframe={timeframe} />}
            {activeTab === "relative-strength" && <RelativeStrength timeframe={timeframe} />}
          </div>
        </div>
      </div>
    </main>
  );
}
