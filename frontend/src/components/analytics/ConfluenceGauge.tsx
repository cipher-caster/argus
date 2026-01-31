"use client";

import { MarketSentimentBar } from "@/components/MarketSentimentBar";
import { ConfluenceResponse, fetchConfluence } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export function ConfluenceGauge() {
  const { data, isLoading, refetch, isRefetching } = useQuery<ConfluenceResponse>({
    queryKey: ["confluence"],
    queryFn: () => fetchConfluence(50),
    refetchInterval: 60000,
  });

  return (
    <MarketSentimentBar
      data={
        data
          ? {
              bullish_pct: data.metrics.bullish_pct,
              bearish_pct: data.metrics.bearish_pct,
              sleeping_pct: data.metrics.sleeping_pct,
              verdict: data.verdict,
            }
          : undefined
      }
      isLoading={isLoading}
      isRefetching={isRefetching}
      onRefresh={async () => {
        await refetch();
      }}
      variant="confluence"
    />
  );
}
