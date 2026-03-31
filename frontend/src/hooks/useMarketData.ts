"use client";

/**
 * React Query hooks for market data
 */

import { fetchOHLCV, fetchProviderInfo, fetchSymbols, fetchTicker, setProvider } from "@/lib/api";
import { fetchTickers } from "@/lib/marketApi";
import { keepPreviousData, useInfiniteQuery, useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

/**
 * Hook for fetching current exchange provider info
 */
export function useProviderInfo() {
  return useQuery({
    queryKey: ["providerInfo"] as const,
    queryFn: fetchProviderInfo,
    staleTime: Infinity, // Provider rarely changes without user action
  });
}

/**
 * Hook to update the exchange provider
 */
export function useSetProvider() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: setProvider,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["providerInfo"] });
      qc.invalidateQueries({ queryKey: ["ohlcv"] });
      qc.invalidateQueries({ queryKey: ["tickers"] });
      qc.invalidateQueries({ queryKey: ["symbols"] });
    },
  });
}

/**
 * Hook for fetching OHLCV candlestick data with infinite scrolling
 */
export function useOHLCV(symbol: string, timeframe: string = "1h", limit: number = 1000, provider?: string) {
  return useInfiniteQuery({
    queryKey: ["ohlcv", symbol, timeframe, limit, provider ?? "binance"] as const,
    queryFn: async ({ pageParam }) => {
      const result = await fetchOHLCV(symbol, timeframe, limit, pageParam, provider);
      return result;
    },
    getNextPageParam: (lastPage) => {
      if (!lastPage.candles || lastPage.candles.length === 0) {
        return undefined;
      }
      const oldestTimestamp = lastPage.candles[0].timestamp;

      // If we got fewer candles than requested, we likely reached the end
      if (lastPage.candles.length < limit) {
        return undefined;
      }

      return oldestTimestamp;
    },
    initialPageParam: undefined as number | undefined,
    refetchInterval: 15000, // Refresh every 15 seconds to stay in sync with ticker
    staleTime: 10000,
    enabled: !!symbol,
  });
}

/**
 * Hook for fetching all basic tickers
 */
export function useTickers() {
  return useQuery({
    queryKey: ["tickers"],
    queryFn: fetchTickers,
    refetchInterval: 30_000, // Refetch every 30s — dashboard tickers
    staleTime: 15_000,
    gcTime: 5 * 60_000,
    placeholderData: keepPreviousData,
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
    staleTime: 3000,
    enabled: !!symbol,
  });
}


