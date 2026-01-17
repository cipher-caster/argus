"use client";

/**
 * React Query hooks for analytics data
 */

import { fetchAnalyticsSymbols, fetchLiquiditySweeps, fetchMarketHealth, fetchMeanReversion, fetchOracleScreener, fetchOracleSignalSummary, fetchRelativeStrength } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

/**
 * Hook for fetching supported analytics symbols
 */
export function useAnalyticsSymbols(limit: number = 20) {
  return useQuery({
    queryKey: ["analytics", "symbols", limit],
    queryFn: () => fetchAnalyticsSymbols(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useOracleScreener(timeframe: string = "1h", limit: number = 50) {
  return useQuery({
    queryKey: ["analytics", "screener", timeframe, limit],
    queryFn: () => fetchOracleScreener(timeframe, limit),
    staleTime: 60000,
  });
}

export function useMarketHealth(timeframe: string = "1h", limit: number = 100) {
  return useQuery({
    queryKey: ["analytics", "market-health", timeframe, limit],
    queryFn: () => fetchMarketHealth(timeframe, limit),
    staleTime: 60000,
  });
}

export function useLiquiditySweeps(timeframe: string = "1h", limit: number = 50) {
  return useQuery({
    queryKey: ["analytics", "liquidity-sweeps", timeframe, limit],
    queryFn: () => fetchLiquiditySweeps(timeframe, limit),
    staleTime: 60000,
  });
}

export function useRelativeStrength(timeframe: string = "1h", limit: number = 50) {
  return useQuery({
    queryKey: ["analytics", "relative-strength", timeframe, limit],
    queryFn: () => fetchRelativeStrength(timeframe, limit),
    staleTime: 60000,
  });
}

export function useContrarianRadar(timeframe: string = "1h", limit: number = 50) {
  return useQuery({
    queryKey: ["analytics", "contrarian-radar", timeframe, limit],
    queryFn: () => fetchMeanReversion(timeframe, limit),
    staleTime: 60000,
  });
}

export function useOracleSignalSummary() {
  return useQuery({
    queryKey: ["analytics", "signal-summary"],
    queryFn: fetchOracleSignalSummary,
    staleTime: 30000,
  });
}
