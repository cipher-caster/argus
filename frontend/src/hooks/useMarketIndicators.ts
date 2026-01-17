import { DashboardIndicators, fetchDashboardIndicators, IndicatorValue, MarketCapStats } from "@/lib/indicatorApi";
import { useQuery } from "@tanstack/react-query";

// Re-export types for convenience
export type { DashboardIndicators, IndicatorValue, MarketCapStats };

export function useMarketIndicators() {
  return useQuery({
    queryKey: ["market-indicators"],
    queryFn: fetchDashboardIndicators,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000, // Auto refresh every minute
  });
}
