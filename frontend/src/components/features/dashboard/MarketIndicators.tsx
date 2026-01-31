"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toaster";
import { useMarketIndicators } from "@/hooks/useMarketIndicators";
import { formatVolume } from "@/lib/formatters";
import { Activity, Bitcoin, Globe, TrendingUp } from "lucide-react";
import { memo } from "react";
import { IndicatorCard } from "./IndicatorCard";

// Tooltip descriptions for each indicator
const TOOLTIPS = {
  volatility: "Measures BTC price volatility over 14 days. Low Vol (<25) = stable market, good for range trading. High Vol (>50) = large price swings, higher risk/reward.",
  adx: "Average Directional Index measures trend strength. Ranging (<20) = no clear trend, wait for breakout. Trending (20-40) = moderate trend. Strong (>40) = powerful trend, trade with direction.",
  rsi: "Average Relative Strength Index (RSI) across top 100 coins. <30 (Oversold) indicates potential bounce. >70 (Overbought) suggests potential pullback.",
  volume: "Total 24h trading volume of top 100 coins. Shows overall market activity. Regime is based on average price change: BULLISH (>2%), NEUTRAL, BEARISH (<-2%).",
  dominance: "BTC's share of total trading volume among top 100 coins. High (>30%) = BTC leading. Normal (15-30%) = balanced. Alt Season (<15%) = altcoins outperforming.",
};

function MarketIndicatorsComponent() {
  const { data, isLoading, refetch, isRefetching } = useMarketIndicators();
  const { toast, dismiss } = useToast();

  const handleRefresh = async () => {
    const id = toast("Refreshing market indicators...", "info");
    await refetch();
    dismiss(id);
    toast("Market indicators refreshed", "success");
  };

  if (isLoading) {
    return (
      <>
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-[180px] rounded-xl" />
        ))}
        <Skeleton className="h-12 rounded-lg" /> {/* Oracle Intelligence compact bar */}
      </>
    );
  }

  const isMarketCap = data?.total_market_cap?.metric_type === "market_cap";
  const domTitle = isMarketCap ? "Market Cap Share" : "Volume Share";

  return (
    <>
      {/* Market ADX Card - Gauge Only */}
      <IndicatorCard
        title="MADX"
        subtitle="Market ADX"
        icon={<TrendingUp size={16} />}
        value={data?.market_adx?.value ?? 0}
        label={data?.market_adx?.label ?? "N/A"}
        tooltip={TOOLTIPS.adx}
        showGauge={true}
        chartColor="#22c55e"
        min={data?.market_adx?.min_value ?? 0}
        max={data?.market_adx?.max_value ?? 100}
        onRefresh={handleRefresh}
        isRefetching={isRefetching}
      />

      {/* Avg Crypto RSI Card - Gauge + Value + Sparkline */}
      <IndicatorCard
        title="Avg Crypto RSI"
        subtitle="Momentum (14)"
        icon={<Activity size={16} />}
        value={data?.average_rsi?.value ?? 0}
        label={data?.average_rsi?.label ?? "N/A"}
        tooltip={TOOLTIPS.rsi}
        showGauge={true}
        gaugeColors={{ low: "#22c55e", high: "#ef4444" }}
        chartColor="#3b82f6"
        max={100}
        onRefresh={handleRefresh}
        isRefetching={isRefetching}
      />

      {/* Total Volume / Market Cap Card - Sparkline Only */}
      <IndicatorCard
        title={isMarketCap ? "Total Market Cap" : "24h Volume"}
        subtitle="Top 100 Coins"
        icon={<Globe size={16} />}
        value={formatVolume(data?.total_market_cap?.value ?? 0)}
        label={data?.total_market_cap?.regime ?? "NEUTRAL"}
        tooltip={isMarketCap ? "Total market capitalization of top 100 coins." : TOOLTIPS.volume}
        showGauge={false}
        chartColor="#a855f7"
        history={data?.total_market_cap?.history ?? []}
        onRefresh={handleRefresh}
        isRefetching={isRefetching}
      />

      {/* BTC Dominance Card - Gauge Only */}
      <IndicatorCard
        title="BTC Dominance"
        subtitle={domTitle}
        icon={<Bitcoin size={16} />}
        value={`${(data?.btc_dominance?.value ?? 0).toFixed(1)}%`}
        label={data?.btc_dominance?.label ?? "N/A"}
        tooltip={isMarketCap ? "BTC's share of Total Market Cap (~50-60% typically)." : TOOLTIPS.dominance}
        showGauge={true}
        gaugeColors={{ low: "#22c55e", high: "#f59e0b" }}
        chartColor="#f59e0b"
        min={data?.btc_dominance?.min_value ?? 10}
        max={data?.btc_dominance?.max_value ?? (isMarketCap ? 70 : 50)}
        onRefresh={handleRefresh}
        isRefetching={isRefetching}
      />
    </>
  );
}

export const MarketIndicators = memo(MarketIndicatorsComponent);
