"use client";

import { fetchOracleStrategy } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

/**
 * Hook for fetching Oracle Strategy analysis for a symbol
 */
export function useStrategyOracle(symbol: string, microTf: string = "1h", macroTf: string = "1d") {
  return useQuery({
    queryKey: ["strategy-oracle", symbol, microTf, macroTf],
    queryFn: () => fetchOracleStrategy(symbol, microTf, macroTf),
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: !!symbol,
    staleTime: 10000,
  });
}
