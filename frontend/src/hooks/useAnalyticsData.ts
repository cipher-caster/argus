"use client";

/**
 * React Query hooks for analytics data
 */

import { fetchAnalyticsSymbols, fetchFundingRate, fetchLongShortRatio, fetchOpenInterest } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

/**
 * Hook for fetching funding rate history
 */
export function useFundingRate(symbol: string = "BTCUSDT", limit: number = 100) {
  return useQuery({
    queryKey: ["analytics", "funding-rate", symbol, limit],
    queryFn: () => fetchFundingRate(symbol, limit),
    staleTime: 60000, // 1 minute
    enabled: !!symbol,
  });
}

/**
 * Hook for fetching open interest history
 */
export function useOpenInterest(symbol: string = "BTCUSDT", period: string = "1h", limit: number = 100) {
  return useQuery({
    queryKey: ["analytics", "open-interest", symbol, period, limit],
    queryFn: () => fetchOpenInterest(symbol, period, limit),
    staleTime: 60000,
    enabled: !!symbol,
  });
}

/**
 * Hook for fetching long/short ratio history
 */
export function useLongShortRatio(symbol: string = "BTCUSDT", period: string = "1h", limit: number = 100) {
  return useQuery({
    queryKey: ["analytics", "long-short-ratio", symbol, period, limit],
    queryFn: () => fetchLongShortRatio(symbol, period, limit),
    staleTime: 60000,
    enabled: !!symbol,
  });
}

/**
 * Hook for fetching supported analytics symbols
 */
export function useAnalyticsSymbols() {
  return useQuery({
    queryKey: ["analytics", "symbols"],
    queryFn: fetchAnalyticsSymbols,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
