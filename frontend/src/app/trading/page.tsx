"use client";

import { PortfolioSummary } from "@/components/trading/PortfolioSummary";
import { PositionsTable } from "@/components/trading/PositionsTable";
import { TradeHistory } from "@/components/trading/TradeHistory";
import { TradingConfigPanel } from "@/components/trading/TradingConfig";
import { EquityCurve } from "@/components/trading/EquityCurve";
import { ActivityFeed } from "@/components/trading/ActivityFeed";
import { useTradingStats } from "@/hooks/useTradingData";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, BarChart3, Activity } from "lucide-react";

function StatsStrip() {
  const { data: stats } = useTradingStats();
  if (!stats || stats.total_trades === 0) return null;

  const items = [
    {
      label: "Win Rate",
      value: stats.win_rate !== null ? `${stats.win_rate}%` : "—",
      positive: (stats.win_rate ?? 0) >= 50,
    },
    {
      label: "Avg Win",
      value: stats.avg_win_pct !== null ? `+${stats.avg_win_pct}%` : "—",
      positive: true,
    },
    {
      label: "Avg Loss",
      value: stats.avg_loss_pct !== null ? `${stats.avg_loss_pct}%` : "—",
      positive: false,
    },
    {
      label: "Profit Factor",
      value: stats.profit_factor !== null ? `${stats.profit_factor}x` : "—",
      positive: (stats.profit_factor ?? 0) >= 1,
    },
    {
      label: "Max DD",
      value: `${stats.max_drawdown_pct}%`,
      positive: stats.max_drawdown_pct < 10,
    },
    {
      label: "Total Trades",
      value: `${stats.total_trades}`,
    },
  ];

  return (
    <div className="grid grid-cols-3 lg:grid-cols-6 gap-3">
      {items.map(item => (
        <div key={item.label} className="bg-card/40 border border-border/30 rounded-xl p-3 text-center">
          <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider mb-0.5">{item.label}</div>
          <div className={cn(
            "text-[15px] font-black",
            item.positive === true && "text-emerald-500",
            item.positive === false && "text-red-500",
          )}>{item.value}</div>
        </div>
      ))}
    </div>
  );
}

export default function TradingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="max-w-[1440px] mx-auto p-6 md:p-8 space-y-5">

        {/* Portfolio summary */}
        <section className="animate-in fade-in slide-in-from-top-2 duration-500">
          <PortfolioSummary />
        </section>

        {/* Stats strip */}
        <section className="animate-in fade-in duration-500 delay-75">
          <StatsStrip />
        </section>

        {/* Main grid */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-5 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="lg:col-span-2 space-y-5">
            <PositionsTable />
            <EquityCurve />
            <TradeHistory />
          </div>
          <div className="space-y-5">
            <TradingConfigPanel />
            <div className="bg-secondary/30 rounded-2xl p-5 border border-border/50 backdrop-blur-sm">
              <ActivityFeed />
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
