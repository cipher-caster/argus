"use client";

/**
 * React Query hook for liquidation heatmap data
 */

import { fetchLiquidationHeatmap, fetchLiquidationSymbols } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

/**
 * Hook for fetching liquidation heatmap data
 */
export function useLiquidationHeatmap(symbol: string = "BTCUSDT", lookbackHours: number = 24) {
  return useQuery({
    queryKey: ["liquidation", "heatmap", symbol, lookbackHours],
    queryFn: () => fetchLiquidationHeatmap(symbol, lookbackHours),
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
    staleTime: 2000,
    enabled: !!symbol,
  });
}

/**
 * Hook for fetching supported liquidation symbols
 */
export function useLiquidationSymbols() {
  return useQuery({
    queryKey: ["liquidation", "symbols"],
    queryFn: fetchLiquidationSymbols,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
