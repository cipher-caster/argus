import { CoinInfo } from "@/lib/marketApi";
import { memo } from "react";
import { Sparkline } from "./Sparkline";

interface StatsCardsProps {
  coins: CoinInfo[];
  isLoading: boolean;
}

import { cn } from "@/lib/utils";

function StatsCardsComponent({ coins, isLoading }: StatsCardsProps) {
  // Generate a mock trend for visualization
  const getMockTrend = (trend: number | null) => {
    const base = 50;
    const count = 10;
    const vals = [base];
    for (let i = 1; i < count; i++) {
      const change = (Math.random() - 0.5) * 5 + (trend || 0) / count;
      vals.push(vals[i - 1] + change);
    }
    return vals;
  };

  // Calculate stats from available coins
  const totalVolume = coins.reduce((acc, coin) => acc + (coin.volume_24h || 0), 0);
  const sorted = [...coins].sort((a, b) => (b.change_24h || 0) - (a.change_24h || 0));
  const topGainer = sorted[0];
  const topLoser = sorted[sorted.length - 1];
  const volLeader = [...coins].sort((a, b) => (b.volume_24h || 0) - (a.volume_24h || 0))[0];

  const formatCurrency = (val: number) => {
    if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
    if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
    return `$${val.toLocaleString()}`;
  };

  const formatPercent = (val: number | null) => {
    if (val === null) return "-";
    return `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;
  };

  const StatCard = ({ title, value, subValue, trend, chartColor }: any) => (
    <div className="bg-secondary border border-border rounded-xl p-4 flex-1 min-w-[240px] shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between mb-3">
        <span className="text-[13px] text-muted-foreground font-bold uppercase tracking-tight">{title}</span>
        {trend !== null && <span className={cn("text-[12px] font-bold px-1.5 py-0.5 rounded", trend >= 0 ? "text-success bg-success/15" : "text-danger bg-danger/15")}>{formatPercent(trend)}</span>}
      </div>
      <div className="flex justify-between items-end">
        <div className="flex flex-col gap-0.5">
          <span className="text-[20px] font-extrabold text-foreground tracking-tighter leading-none">{value}</span>
          <span className="text-[12px] text-muted-foreground font-medium">{subValue}</span>
        </div>
        <div className="w-20 h-8 opacity-80">
          <Sparkline data={getMockTrend(trend)} width={80} height={32} color={chartColor} />
        </div>
      </div>
    </div>
  );

  if (isLoading || coins.length === 0) {
    return (
      <div className="flex flex-wrap gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-secondary border border-border rounded-xl flex-1 min-w-[240px] animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-4 mb-6">
      <StatCard title="24h Volume (Top 50)" value={formatCurrency(totalVolume)} subValue="Global Market Activity" trend={null} chartColor="hsl(var(--primary))" />
      <StatCard title="Top Gainer" value={topGainer?.symbol} subValue={formatCurrency(topGainer?.price || 0)} trend={topGainer?.change_24h} chartColor="hsl(var(--success))" />
      <StatCard title="Top Loser" value={topLoser?.symbol} subValue={formatCurrency(topLoser?.price || 0)} trend={topLoser?.change_24h} chartColor="hsl(var(--danger))" />
      <StatCard title="Vol Leader" value={volLeader?.symbol} subValue={formatCurrency(volLeader?.volume_24h || 0)} trend={volLeader?.change_24h} chartColor="#f59e0b" />
    </div>
  );
}

export const StatsCards = memo(StatsCardsComponent);
