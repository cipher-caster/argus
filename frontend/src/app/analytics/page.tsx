"use client";

import { cn } from "@/lib/utils";
import { History, Info, Sparkles } from "lucide-react";
import dynamic from "next/dynamic";
import { useState } from "react";

const BestSetups = dynamic(() => import("@/components/analytics").then((mod) => ({ default: mod.BestSetups })), {
  loading: () => <div className="h-[500px] flex items-center justify-center text-muted-foreground">Finding setups…</div>,
});

const SignalLog = dynamic(() => import("@/components/analytics").then((mod) => ({ default: mod.SignalLog })), {
  loading: () => <div className="h-[400px] flex items-center justify-center text-muted-foreground">Loading Signal Log…</div>,
});

type ChartType = "best-setups" | "signal-log";

const MENU_ITEMS: { id: ChartType; label: string; icon: React.ElementType }[] = [
  { id: "best-setups", label: "Best Setups", icon: Sparkles },
  { id: "signal-log", label: "Signal Log", icon: History },
];

const CHART_INFO: Record<ChartType, { title: string; description: string | string[] }> = {
  "best-setups": {
    title: "Best Setups",
    description: "Titan signals filtered by market regime. In BULL: longs prioritized. In BEAR: shorts prioritized. Conviction based on Titan confidence + regime alignment.",
  },
  "signal-log": {
    title: "Signal Log",
    description: [
      "Live — 4H candle close, watchlist coins only.",
      "Scanner — best-setups snapshots, top 100 coins.",
      "Backtest — historical replay.",
      "Resolves as WIN, LOSS, REVIEW (7d), or REJECTED.",
      "Shows fired/resolved timestamps, regime changes, and BTC price at resolution.",
    ],
  },
};

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<ChartType>("best-setups");
  const [timeframe, setTimeframe] = useState<string>("4h");

  const TIMEFRAMES = [
    { id: "1h", label: "1H" },
    { id: "4h", label: "4H" },
    { id: "1d", label: "1D" },
  ];

  const info = CHART_INFO[activeTab];

  return (
    <main className="max-w-[1440px] mx-auto p-6 md:p-8 space-y-10 min-h-screen">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 animate-in fade-in slide-in-from-top-2 duration-500">
        <div className="space-y-1">
          <h1 className="text-3xl font-black tracking-tight italic">QUANT ANALYTICS</h1>
          <p className="text-muted-foreground text-sm font-medium tracking-wide uppercase opacity-70">
            High-conviction setups only. No noise.
          </p>
        </div>

        <div className="flex bg-secondary/30 p-1 rounded-xl border border-border/50 backdrop-blur-sm self-start md:self-auto">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.id}
              onClick={() => setTimeframe(tf.id)}
              className={cn(
                "px-4 py-2 rounded-lg text-[11px] font-black uppercase tracking-wider transition-all duration-300",
                timeframe === tf.id
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              )}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start animate-in fade-in slide-in-from-bottom-4 duration-700">
        {/* Sidebar */}
        <aside className="lg:col-span-1 space-y-4 sticky top-8">
          <nav className="bg-secondary/30 rounded-2xl p-2 border border-border/50 backdrop-blur-sm">
            {MENU_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-300 group relative overflow-hidden",
                  activeTab === item.id
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                    : "hover:bg-primary/10 text-muted-foreground hover:text-foreground hover:translate-x-1"
                )}
              >
                {activeTab === item.id && <div className="absolute left-0 top-0 bottom-0 w-1 bg-white/20" />}
                <item.icon
                  size={18}
                  className={cn("transition-transform duration-300", activeTab === item.id ? "scale-110" : "group-hover:scale-110")}
                />
                <span className="text-[13px] font-bold uppercase tracking-tight">{item.label}</span>
              </button>
            ))}
          </nav>

          <div className="bg-secondary/30 rounded-2xl p-5 border border-border/50 space-y-3 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-primary">
              <Info size={16} />
              <h3 className="text-xs font-black uppercase tracking-widest">{info.title}</h3>
            </div>
            {Array.isArray(info.description) ? (
              <ul className="space-y-1.5">
                {info.description.map((line, i) => (
                  <li key={i} className="text-[11px] text-muted-foreground leading-relaxed font-medium flex gap-2">
                    <span className="text-primary/50 mt-px">•</span>
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[11px] text-muted-foreground leading-relaxed font-medium">{info.description}</p>
            )}
          </div>
        </aside>

        {/* Content */}
        <div className="lg:col-span-3 min-h-[500px] bg-secondary/10 rounded-3xl border border-border/30 overflow-hidden shadow-2xl shadow-black/20">
          <div className="p-6 md:p-8">
            {activeTab === "best-setups" && <BestSetups timeframe={timeframe} />}
            {activeTab === "signal-log" && <SignalLog />}
          </div>
        </div>
      </div>
    </main>
  );
}
