"use client";

import { fetchTitanStrategy } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export function useStrategyTitan(symbol: string, timeframe: string = "4h", provider?: string) {
  return useQuery({
    queryKey: ["strategy-titan", symbol, timeframe, provider ?? "okx"],
    queryFn: () => fetchTitanStrategy(symbol, timeframe, provider),
    staleTime: 30_000,
    refetchInterval: 30_000,
    enabled: !!symbol,
  });
}
