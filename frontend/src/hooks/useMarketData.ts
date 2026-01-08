"use client";

/**
 * React Query hooks for market data
 */

import { fetchOHLCV, fetchProviderInfo, fetchSymbols, fetchTicker } from "@/lib/api";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";

/**
 * Hook for fetching OHLCV candlestick data with infinite scrolling
 */
export function useOHLCV(symbol: string, timeframe: string = "1h", limit: number = 1000) {
  return useInfiniteQuery({
    queryKey: ["ohlcv", symbol, timeframe, limit] as const,
    queryFn: async ({ pageParam }) => {
      console.log(`[useOHLCV] Fetching page, pageParam=${pageParam}`);
      const result = await fetchOHLCV(symbol, timeframe, limit, pageParam);
      console.log(`[useOHLCV] Got ${result.candles?.length || 0} candles`);
      return result;
    },
    getNextPageParam: (lastPage) => {
      console.log(`[useOHLCV] getNextPageParam: candles=${lastPage.candles?.length}, limit=${limit}`);
      if (!lastPage.candles || lastPage.candles.length === 0) {
        console.log("[useOHLCV] No candles returned, no more pages");
        return undefined;
      }
      const oldestTimestamp = lastPage.candles[0].timestamp;

      // If we got fewer candles than requested, we likely reached the end
      if (lastPage.candles.length < limit) {
        return undefined;
      }

      console.log(`[useOHLCV] Next page param: ${oldestTimestamp}`);
      return oldestTimestamp;
    },
    initialPageParam: undefined as number | undefined,
    refetchInterval: 15000, // Refresh every 15 seconds to stay in sync with ticker
    staleTime: 10000,
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
