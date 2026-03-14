"use client";

import { fetchTitanStrategy } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export function useStrategyTitan(symbol: string, timeframe: string = "4h") {
  return useQuery({
    queryKey: ["strategy-titan", symbol, timeframe],
    queryFn: () => fetchTitanStrategy(symbol, timeframe),
    staleTime: 30_000,
    refetchInterval: 30_000,
    enabled: !!symbol,
  });
}
