import { Sparkline } from "@/components/features/chart/Sparkline";
import { Skeleton } from "@/components/ui/skeleton";
import { CoinInfo } from "@/lib/marketApi";
import { memo } from "react";

interface StatsCardsProps {
  coins: CoinInfo[];
  isLoading: boolean;
}

import { formatChange, formatVolume } from "@/lib/formatters";
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

interface StatCardProps {
  title: string;
  value: string | undefined;
  subValue: string;
  trend: number | null | undefined;
  chartColor: string;
}

  const StatCard = ({ title, value, subValue, trend, chartColor }: StatCardProps) => (
    <div className="bg-secondary border border-border rounded-xl p-4 flex-1 min-w-[240px] shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between mb-3">
        <span className="text-[13px] text-muted-foreground font-bold uppercase tracking-tight">{title}</span>
        {trend != null && <span className={cn("text-[12px] font-bold px-1.5 py-0.5 rounded", trend >= 0 ? "text-success bg-success/15" : "text-danger bg-danger/15")}>{formatChange(trend)}</span>}
      </div>
      <div className="flex justify-between items-end">
        <div className="flex flex-col gap-0.5">
          <span className="text-[20px] font-extrabold text-foreground tracking-tighter leading-none">{value}</span>
          <span className="text-[12px] text-muted-foreground font-medium">{subValue}</span>
        </div>
        <div className="w-20 h-8 opacity-80">
          <Sparkline data={getMockTrend(trend ?? null)} width={80} height={32} color={chartColor} />
        </div>
      </div>
    </div>
  );

  if (isLoading || coins.length === 0) {
    return (
      <div className="flex flex-wrap gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-[88px] flex-1 min-w-[240px] rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-4 mb-6">
      <StatCard title="24h Volume (Top 50)" value={formatVolume(totalVolume)} subValue="Global Market Activity" trend={null} chartColor="hsl(var(--primary))" />
      <StatCard title="Top Gainer" value={topGainer?.symbol} subValue={formatVolume(topGainer?.price || 0)} trend={topGainer?.change_24h} chartColor="hsl(var(--success))" />
      <StatCard title="Top Loser" value={topLoser?.symbol} subValue={formatVolume(topLoser?.price || 0)} trend={topLoser?.change_24h} chartColor="hsl(var(--danger))" />
      <StatCard title="Vol Leader" value={volLeader?.symbol} subValue={formatVolume(volLeader?.volume_24h || 0)} trend={volLeader?.change_24h} chartColor="#f59e0b" />
    </div>
  );
}

export const StatsCards = memo(StatsCardsComponent);
