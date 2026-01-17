"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useMarketIndicators } from "@/hooks/useMarketIndicators";
import { formatChange, formatVolume } from "@/lib/formatters";
import { Bitcoin, Globe, TrendingUp } from "lucide-react";
import { memo } from "react";
import { IndicatorCard } from "./IndicatorCard";

// Tooltip descriptions for each indicator
const TOOLTIPS = {
  volatility: "Measures BTC price volatility over 14 days. Low Vol (<25) = stable market, good for range trading. High Vol (>50) = large price swings, higher risk/reward.",
  adx: "Average Directional Index measures trend strength. Ranging (<20) = no clear trend, wait for breakout. Trending (20-40) = moderate trend. Strong (>40) = powerful trend, trade with direction.",
  volume: "Total 24h trading volume of top 100 coins. Shows overall market activity. Regime is based on average price change: BULLISH (>2%), NEUTRAL, BEARISH (<-2%).",
  dominance: "BTC's share of total trading volume among top 100 coins. High (>30%) = BTC leading. Normal (15-30%) = balanced. Alt Season (<15%) = altcoins outperforming.",
};

function MarketIndicatorsComponent() {
  const { data, isLoading } = useMarketIndicators();

  if (isLoading) {
    return (
      <>
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-[180px] rounded-xl" />
        ))}
      </>
    );
  }

  const isMarketCap = data?.total_market_cap?.metric_type === "market_cap";
  const domTitle = isMarketCap ? "Market Cap Share" : "Volume Share";

  return (
    <>
      {/* Market ADX Card */}
      <IndicatorCard
        title="MADX"
        subtitle="Market ADX"
        icon={<TrendingUp size={16} />}
        value={data?.market_adx?.value ?? 0}
        label={data?.market_adx?.label ?? "N/A"}
        tooltip={TOOLTIPS.adx}
        showGauge={true}
        chartColor="#22c55e"
        history={data?.market_adx?.history ?? []}
        min={data?.market_adx?.min_value ?? 0}
        max={data?.market_adx?.max_value ?? 100}
      />

      {/* Total Volume / Market Cap Card */}
      <IndicatorCard
        title={isMarketCap ? "Total Market Cap" : "24h Volume"}
        subtitle="Top 100 Coins"
        icon={<Globe size={16} />}
        value={formatVolume(data?.total_market_cap?.value ?? 0)}
        label={data?.total_market_cap?.regime ?? "NEUTRAL"}
        tooltip={isMarketCap ? "Total market capitalization of top 100 coins." : TOOLTIPS.volume}
        showGauge={true}
        chartColor="#a855f7"
        history={data?.total_market_cap?.history ?? []}
        min={data?.total_market_cap?.min_value ?? 0}
        max={data?.total_market_cap?.max_value ?? 0}
        extraContent={
          <div className="flex gap-4 text-xs mb-2">
            <span className={data?.total_market_cap?.change_1d && data.total_market_cap.change_1d >= 0 ? "text-green-400" : "text-red-400"}>Avg {formatChange(data?.total_market_cap?.change_1d ?? 0)}</span>
            <span className="text-muted-foreground">{data?.total_market_cap?.regime_detail}</span>
          </div>
        }
      />

      {/* BTC Dominance Card */}
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
        history={data?.btc_dominance?.history ?? []}
        min={data?.btc_dominance?.min_value ?? 10}
        max={data?.btc_dominance?.max_value ?? (isMarketCap ? 70 : 50)}
      />
    </>
  );
}

export const MarketIndicators = memo(MarketIndicatorsComponent);
