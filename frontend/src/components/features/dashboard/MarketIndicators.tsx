"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useMarketIndicators } from "@/hooks/useMarketIndicators";
import { formatChange, formatVolume } from "@/lib/formatters";
import { Activity, Bitcoin, Globe, TrendingUp } from "lucide-react";
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
      <div className="flex flex-wrap gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-[180px] flex-1 min-w-[260px] rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-4 mb-6">
      {/* BTC Volatility Card */}
      <IndicatorCard
        title="BTC Volatility"
        icon={<Activity size={16} />}
        value={data?.btc_volatility?.value ?? 0}
        label={data?.btc_volatility?.label ?? "N/A"}
        tooltip={TOOLTIPS.volatility}
        showGauge={true}
        gaugeColors={{ low: "#06b6d4", high: "#ef4444" }}
        chartColor="#06b6d4"
        min={data?.btc_volatility?.min_value ?? 1}
        max={data?.btc_volatility?.max_value ?? 100}
        history={data?.btc_volatility?.history ?? []}
      />

      {/* Market ADX Card */}
      <IndicatorCard
        title="MADX"
        subtitle="Market ADX"
        icon={<TrendingUp size={16} />}
        value={data?.market_adx?.value ?? 0}
        label={data?.market_adx?.label ?? "N/A"}
        tooltip={TOOLTIPS.adx}
        showGauge={false}
        chartColor="#22c55e"
        min={data?.market_adx?.min_value ?? 0}
        max={data?.market_adx?.max_value ?? 100}
        history={data?.market_adx?.history ?? []}
      />

      {/* Total Volume Card */}
      <IndicatorCard
        title="24h Volume"
        subtitle="Top 100 Coins"
        icon={<Globe size={16} />}
        value={formatVolume(data?.total_market_cap?.value ?? 0)}
        label={data?.total_market_cap?.regime ?? "NEUTRAL"}
        tooltip={TOOLTIPS.volume}
        showGauge={false}
        chartColor="#a855f7"
        min={data?.total_market_cap?.min_value ?? 0}
        max={data?.total_market_cap?.max_value ?? 0}
        history={data?.total_market_cap?.history ?? []}
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
        subtitle="Volume Share"
        icon={<Bitcoin size={16} />}
        value={`${(data?.btc_dominance?.value ?? 0).toFixed(1)}%`}
        label={data?.btc_dominance?.label ?? "N/A"}
        tooltip={TOOLTIPS.dominance}
        showGauge={true}
        gaugeColors={{ low: "#22c55e", high: "#f59e0b" }}
        chartColor="#f59e0b"
        min={data?.btc_dominance?.min_value ?? 10}
        max={data?.btc_dominance?.max_value ?? 50}
        history={data?.btc_dominance?.history ?? []}
      />
    </div>
  );
}

export const MarketIndicators = memo(MarketIndicatorsComponent);
