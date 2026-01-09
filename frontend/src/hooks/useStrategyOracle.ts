"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchOracleStrategy } from "@/lib/api";

/**
 * Hook for fetching Oracle Strategy analysis for a symbol
 */
export function useStrategyOracle(
  symbol: string,
  microTf: string = "1h",
  macroTf: string = "1d",
  mode: string = "prophet"
) {
  return useQuery({
    queryKey: ["strategy-oracle", symbol, microTf, macroTf, mode],
    queryFn: () => fetchOracleStrategy(symbol, microTf, macroTf, mode),
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: !!symbol,
    staleTime: 10000,
  });
}
