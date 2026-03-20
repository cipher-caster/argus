"use client";

/**
 * React Query hooks for analytics data
 * Optimized with stale-while-revalidate for better UX
 */

import { fetchAnalyticsSymbols, fetchBacktestStats, fetchBestSetups, fetchMeanReversion, fetchOracleScreener, fetchOracleSignalSummary, fetchSignalLog, fetchSignalLogConfig, fetchTitanRadar, updateSignalLogConfig, SignalLogConfig } from "@/lib/api";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

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

export function useBestSetups(timeframe: string = "4h", limit: number = 50) {
  return useQuery({
    queryKey: ["analytics", "best-setups", timeframe, limit],
    queryFn: () => fetchBestSetups(timeframe, limit),
    staleTime: 300_000, // 5 min — backend cache is 6 min, pre-warmed every 5 min
    gcTime: 10 * 60_000,
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
  });
}

export function useOracleScreener(timeframe: string = "4h", limit: number = 50) {
  return useQuery({
    queryKey: ["analytics", "screener", timeframe, limit],
    queryFn: () => fetchOracleScreener(timeframe, limit),
    staleTime: 120_000, // 2 minutes - matches backend cache (180s)
    gcTime: 5 * 60_000, // Keep in cache for 5 min
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData, // Show old data while fetching new
  });
}


export function useContrarianRadar(timeframe: string = "4h", limit: number = 50) {
  return useQuery({
    queryKey: ["analytics", "contrarian-radar", timeframe, limit],
    queryFn: () => fetchMeanReversion(timeframe, limit),
    staleTime: 120_000, // 2 minutes
    gcTime: 5 * 60_000,
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
  });
}

export function useOracleSignalSummary() {
  return useQuery({
    queryKey: ["analytics", "signal-summary"],
    queryFn: fetchOracleSignalSummary,
    staleTime: 60_000, // 1 minute - lighter summary data
    gcTime: 5 * 60_000,
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
  });
}

export function useTitanRadar(limit: number = 50, timeframe: string = "4h") {
  return useQuery({
    queryKey: ["analytics", "titan-radar", limit, timeframe],
    queryFn: () => fetchTitanRadar(limit, timeframe),
    staleTime: 120_000, // 2 minutes
    gcTime: 5 * 60_000,
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
  });
}

export function useSignalLog(symbol?: string, source?: string, limit: number = 50, offset: number = 0) {
  return useQuery({
    queryKey: ["analytics", "signal-log", symbol, source, limit, offset],
    queryFn: () => fetchSignalLog(symbol, source, limit, offset),
    staleTime: 60_000, // 1 minute — resolution job runs hourly, logging every 5 min
    gcTime: 5 * 60_000,
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
  });
}

export function useSignalLogConfig() {
  return useQuery({
    queryKey: ["signal-log-config"],
    queryFn: fetchSignalLogConfig,
    staleTime: 5 * 60_000,
  });
}

export function useBacktestStats() {
  return useQuery({
    queryKey: ["analytics", "backtest-stats"],
    queryFn: fetchBacktestStats,
    staleTime: 10 * 60_000, // 10 min — backtest data rarely changes
  });
}

export function useUpdateSignalLogConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: updateSignalLogConfig,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["signal-log-config"] });
    },
  });
}
