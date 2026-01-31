"use client";

import { MarketSentimentBar } from "@/components/MarketSentimentBar";
import { useOracleSignalSummary } from "@/hooks/useAnalytics";

export function OracleSignalSummary() {
  const { data, isLoading, error, refetch, isRefetching } = useOracleSignalSummary();

  return (
    <MarketSentimentBar
      data={
        data
          ? {
              bullish_pct: data.bullish_pct,
              bearish_pct: data.bearish_pct,
              market_state: data.market_state,
              top_signals: data.top_signals,
            }
          : undefined
      }
      isLoading={isLoading}
      isRefetching={isRefetching}
      onRefresh={refetch}
      error={error}
      variant="oracle"
    />
  );
}
