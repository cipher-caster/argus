"use client";

/**
 * React Query hooks for indicators
 */

import { calculateIndicators, fetchIndicators } from "@/lib/indicatorApi";
import { useIndicatorStore } from "@/stores/indicatorStore";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

/**
 * Hook for fetching available indicators and populating the store
 */
export function useAvailableIndicators() {
  const setAvailableIndicators = useIndicatorStore((s) => s.setAvailableIndicators);

  const query = useQuery({
    queryKey: ["available-indicators"],
    queryFn: fetchIndicators,
    staleTime: Infinity, // Indicators list doesn't change
  });

  // Update store when data loads
  useEffect(() => {
    if (query.data) {
      setAvailableIndicators(query.data);
    }
  }, [query.data, setAvailableIndicators]);

  return query;
}

/**
 * Hook for calculating indicators based on current store state
 */
export function useCalculatedIndicators(symbol: string, timeframe: string) {
  const indicators = useIndicatorStore((s) => s.indicators);
  const visibleIndicators = indicators.filter((i) => i.visible);

  return useQuery({
    queryKey: ["calculated-indicators", symbol, timeframe, visibleIndicators.map((i) => `${i.type}-${JSON.stringify(i.params)}`)],
    queryFn: () => {
      if (visibleIndicators.length === 0) {
        return { symbol, timeframe, results: [] };
      }

      return calculateIndicators(
        symbol,
        timeframe,
        visibleIndicators.map((i) => ({ type: i.type, params: i.params }))
      );
    },
    refetchInterval: 60000, // Refetch with OHLCV
    staleTime: 30000,
    enabled: visibleIndicators.length > 0,
  });
}
