"use client";

/**
 * React Query hooks for market data
 */

import { fetchOHLCV, fetchProviderInfo, fetchSymbols, fetchTicker } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

/**
 * Hook for fetching OHLCV candlestick data
 */
export function useOHLCV(symbol: string, timeframe: string = "1h", limit: number = 300) {
  return useQuery({
    queryKey: ["ohlcv", symbol, timeframe, limit],
    queryFn: () => fetchOHLCV(symbol, timeframe, limit),
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000, // Consider data fresh for 30 seconds
    enabled: !!symbol,
  });
}

/**
 * Hook for fetching available symbols
 */
export function useSymbols() {
  return useQuery({
    queryKey: ["symbols"],
    queryFn: fetchSymbols,
    staleTime: 5 * 60 * 1000, // Cache symbols for 5 minutes
  });
}

/**
 * Hook for fetching current ticker price
 */
export function useTicker(symbol: string) {
  return useQuery({
    queryKey: ["ticker", symbol],
    queryFn: () => fetchTicker(symbol),
    refetchInterval: 5000, // Refetch every 5 seconds
    enabled: !!symbol,
  });
}

/**
 * Hook for fetching provider info
 */
export function useProvider() {
  return useQuery({
    queryKey: ["provider"],
    queryFn: fetchProviderInfo,
    staleTime: Infinity, // Provider doesn't change
  });
}
